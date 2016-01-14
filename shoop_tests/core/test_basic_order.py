# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.utils.timezone import now

from shoop.core.models import (
    get_person_contact, Order, OrderLine, OrderLineTax, OrderLineType
)
from shoop.core.shortcuts import update_order_line_from_product
from shoop.default_tax.module import DefaultTaxModule
from shoop.testing.factories import (
    get_address, get_default_payment_method, get_default_product,
    get_default_shipping_method, get_default_supplier, get_default_tax,
    get_initial_order_status, get_shop
)


def create_order(request, creator, customer, product):
    billing_address = get_address().to_immutable()
    shipping_address = get_address(name="Shippy Doge").to_immutable()
    shipping_address.save()
    shop = request.shop
    order = Order(
        creator=creator,
        customer=customer,
        shop=shop,
        payment_method=get_default_payment_method(),
        shipping_method=get_default_shipping_method(),
        billing_address=billing_address,
        shipping_address=shipping_address,
        order_date=now(),
        status=get_initial_order_status(),
        currency=shop.currency,
        prices_include_tax=shop.prices_include_tax,
    )
    order.full_clean()
    order.save()
    supplier = get_default_supplier()
    product_order_line = OrderLine(order=order)
    update_order_line_from_product(
        pricing_context=request,
        order_line=product_order_line,
        product=product,
        quantity=5,
        supplier=supplier)
    product_order_line.base_unit_price = shop.create_price(100)
    assert product_order_line.price.value > 0
    product_order_line.save()

    line_tax = get_line_taxes_for(product_order_line)[0]

    product_order_line.taxes.add(OrderLineTax.from_tax(
        tax=line_tax.tax,
        base_amount=line_tax.base_amount,
        order_line=product_order_line,
    ))

    discount_order_line = OrderLine(order=order, quantity=1, type=OrderLineType.OTHER)
    discount_order_line.discount_amount = shop.create_price(30)
    assert discount_order_line.discount_amount.value == 30
    assert discount_order_line.price.value == -30
    assert discount_order_line.base_unit_price.value == 0
    discount_order_line.save()

    order.cache_prices()
    order.check_all_verified()
    order.save()
    base = 5 * shop.create_price(100).amount
    discount = shop.create_price(30).amount
    tax_value = line_tax.amount
    if not order.prices_include_tax:
        assert order.taxless_total_price.amount == base - discount
        assert order.taxful_total_price.amount == base + tax_value - discount
    else:
        assert_almost_equal(order.taxless_total_price.amount, base - tax_value - discount)
        assert_almost_equal(order.taxful_total_price.amount, base - discount)

    shipment = order.create_shipment_of_all_products(supplier=supplier)
    assert shipment.total_products == 5, "All products were shipped"
    assert shipment.weight == product.net_weight * 5, "Gravity works"
    assert not order.get_unshipped_products(), "Nothing was left in the warehouse"

    order.create_payment(order.taxful_total_price)
    assert order.is_paid()
    assert Order.objects.paid().filter(pk=order.pk).exists(), "It was paid! Honestly!"


def assert_almost_equal(x, y):
    assert abs(x - y).value <= 0.005


def get_line_taxes_for(order_line):
    get_default_tax()  # Creates the Tax and TaxRule
    tax_module = DefaultTaxModule()
    tax_ctx = tax_module.get_context_from_order_source(order_line.order)
    product = order_line.product
    price = order_line.price
    taxed_price = tax_module.get_taxed_price_for(tax_ctx, product, price)
    return taxed_price.taxes


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["taxful", "taxless"])
def test_basic_order(rf, admin_user, mode):
    prices_include_tax = (mode == "taxful")
    shop = get_shop(prices_include_tax=prices_include_tax)

    request = rf.get('/')
    request.shop = shop
    product = get_default_product()
    customer = get_person_contact(admin_user)
    for x in range(10):
        create_order(request, creator=admin_user, customer=customer, product=product)
    assert Order.objects.filter(customer=customer).count() == 10
