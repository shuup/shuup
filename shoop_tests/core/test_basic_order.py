# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from decimal import Decimal
from django.utils.timezone import now

import pytest
from shoop.core import taxing
from shoop.core.models import Order, OrderLine, OrderLineType, get_person_contact, OrderStatus
from shoop.core.models.order_lines import OrderLineTax
from shoop.core.pricing import TaxfulPrice, TaxlessPrice
from shoop.core.shortcuts import update_order_line_from_product
from shoop.testing.factories import get_address, get_default_payment_method, get_default_shipping_method, \
    get_default_supplier, get_default_product, get_default_shop, get_initial_order_status, get_default_tax
from shoop.simple_pricing.models import SimpleProductPrice

def create_order(request, creator, customer, product):
    billing_address = get_address()
    shipping_address = get_address(name="Shippy Doge")
    shipping_address.save()
    order = Order(
        creator=creator,
        customer=customer,
        shop=get_default_shop(),
        payment_method=get_default_payment_method(),
        shipping_method=get_default_shipping_method(),
        billing_address=billing_address,
        shipping_address=shipping_address,
        order_date=now(),
        status=get_initial_order_status()
    )
    order.full_clean()
    order.save()
    supplier = get_default_supplier()
    product_order_line = OrderLine(order=order)
    update_order_line_from_product(order_line=product_order_line, product=product, request=request, quantity=5, supplier=supplier)
    product_order_line.unit_price = TaxlessPrice(100)
    assert product_order_line.taxful_total_price.amount > 0
    product_order_line.save()
    product_order_line.taxes.add(OrderLineTax.from_tax(get_default_tax(), product_order_line.taxless_total_price))

    discount_order_line = OrderLine(order=order, quantity=1, type=OrderLineType.OTHER)
    discount_order_line.total_discount = TaxfulPrice(30)
    assert discount_order_line.taxful_total_discount.amount == 30
    assert discount_order_line.taxful_total_price.amount == -30
    assert discount_order_line.taxful_unit_price.amount == 0
    discount_order_line.save()

    order.cache_prices()
    order.check_all_verified()
    order.save()
    base_amount = 5 * 100
    tax_value = get_default_tax().calculate_amount(base_amount)
    assert order.taxful_total_price == base_amount + tax_value - 30, "Math works"

    shipment = order.create_shipment_of_all_products(supplier=supplier)
    assert shipment.total_products == 5, "All products were shipped"
    assert shipment.weight == product.net_weight * 5, "Gravity works"
    assert not order.get_unshipped_products(), "Nothing was left in the warehouse"

    order.create_payment(order.taxful_total_price)
    assert order.is_paid()
    assert Order.objects.paid().filter(pk=order.pk).exists(), "It was paid! Honestly!"


@pytest.mark.django_db
def test_basic_order(rf, admin_user):
    request = rf.get('/')
    product = get_default_product()
    SimpleProductPrice.objects.create(product=product, group=None, price=Decimal("100.00"), includes_tax=False)
    customer = get_person_contact(admin_user)
    for x in range(10):
        create_order(request, creator=admin_user, customer=customer, product=product)
    assert Order.objects.filter(customer=customer).count() == 10
