# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.utils.timezone import now

import pytest
from shoop.core.excs import ImmutabilityError, NoProductsToShipException, NoPaymentToCreateException
from shoop.core.models import Order, OrderStatus, OrderLine, OrderLineType
from shoop.core.models.order_lines import OrderLineTax
from shoop.core.models.orders import ShippingStatus
from shoop.core.pricing import TaxlessPrice, TaxfulPrice
from shoop.utils.money import Money
from shoop.testing.factories import (get_address, get_default_shop, get_default_product,
    get_default_supplier, create_order_with_product, create_empty_order, get_initial_order_status, get_default_tax)
import six


@pytest.mark.django_db
@pytest.mark.parametrize("save", (False, True))
def test_order_address_immutability_unsaved_address(save):
    billing_address = get_address()
    if save:
        billing_address.save()
    order = Order(
        shop=get_default_shop(),
        billing_address=billing_address,
        order_date=now(),
        status=get_initial_order_status()
    )
    order.save()
    order.billing_address.name = "Mute Doge"
    with pytest.raises(ImmutabilityError):
        order.billing_address.save()


@pytest.mark.django_db
def test_broken_order_lines():
    with pytest.raises(ValidationError):
        OrderLine(type=OrderLineType.PRODUCT).save()

    with pytest.raises(ValidationError):
        OrderLine(product=get_default_product(), type=OrderLineType.PRODUCT, supplier=None).save()

    with pytest.raises(ValidationError):
        OrderLine(product=get_default_product(), type=OrderLineType.OTHER).save()

    with pytest.raises(ValidationError):
        OrderLine(product=get_default_product(), type=OrderLineType.OTHER, tax_rate=3).save()


@pytest.mark.django_db
def test_line_discount():
    order = create_empty_order(prices_include_tax=False)
    order.save()
    currency = order.shop.currency
    ol = OrderLine(
        order=order,
        type=OrderLineType.OTHER,
        quantity=5,
        text="Thing"
    )
    ol.discount_amount = order.shop.create_price(50)
    ol.base_unit_price = order.shop.create_price(40)
    ol.save()
    ol.taxes.add(OrderLineTax.from_tax(
        get_default_tax(), ol.taxless_total_price.amount, order_line=ol))
    assert ol.taxless_discount_amount == order.shop.create_price(50)
    assert ol.taxful_discount_amount == TaxfulPrice(75, currency)
    assert ol.taxless_total_price == order.shop.create_price(150)
    assert ol.taxful_total_price == TaxfulPrice(150 + 75, currency)
    assert ol.taxless_base_unit_price == order.shop.create_price(40)
    assert ol.taxful_base_unit_price == TaxfulPrice(60, currency)
    assert "Thing" in six.text_type(ol)


@pytest.mark.django_db
def test_line_discount_more():
    order = create_empty_order()
    order.save()
    ol = OrderLine(order=order, type=OrderLineType.OTHER)
    ol.quantity = 5
    ol.base_unit_price = order.shop.create_price(30)
    ol.discount_amount = order.shop.create_price(50)
    ol.save()
    currency = order.shop.currency
    assert ol.taxless_base_unit_price == TaxlessPrice(30, currency)
    assert ol.taxless_discount_amount == TaxlessPrice(50, currency)
    assert ol.taxless_total_price == TaxlessPrice(5 * 30 - 50, currency)
    ol.taxes.add(OrderLineTax.from_tax(
        get_default_tax(), ol.taxless_total_price.amount, order_line=ol))
    assert ol.taxless_discount_amount == TaxlessPrice(50, currency)
    assert ol.taxful_discount_amount == TaxfulPrice(75, currency)
    assert ol.taxless_total_price == TaxlessPrice(100, currency)
    assert ol.taxful_total_price == TaxfulPrice(150, currency)
    assert ol.taxless_base_unit_price == TaxlessPrice(30, currency)
    assert ol.taxful_base_unit_price == TaxfulPrice(45, currency)


@pytest.mark.django_db
def test_basic_order():
    PRODUCTS_TO_SEND = 10
    product = get_default_product()
    supplier = get_default_supplier()
    order = create_order_with_product(
        product,
        supplier=supplier,
        quantity=PRODUCTS_TO_SEND,
        taxless_base_unit_price=10,
        tax_rate=Decimal("0.5")
    )
    assert order.shop.prices_include_tax is False
    price = order.shop.create_price
    currency = order.currency

    discount_order_line = OrderLine(order=order, quantity=1, type=OrderLineType.OTHER)
    discount_order_line.discount_amount = price(30)
    assert discount_order_line.total_price == price(-30)
    discount_order_line.save()

    order.cache_prices()
    order.check_all_verified()
    order.save()
    assert order.taxful_total_price == TaxfulPrice(PRODUCTS_TO_SEND * (10 + 5) - 30, currency)
    shipment = order.create_shipment_of_all_products(supplier=supplier)
    assert shipment.total_products == PRODUCTS_TO_SEND, "All products were shipped"
    assert shipment.weight == product.net_weight * PRODUCTS_TO_SEND, "Gravity works"
    assert not order.get_unshipped_products(), "Nothing was left in the warehouse"
    order.shipping_status = ShippingStatus.FULLY_SHIPPED
    order.create_payment(order.taxful_total_price)
    assert order.payments.exists(), "A payment was created"
    with pytest.raises(NoPaymentToCreateException):
        order.create_payment(Money(6, currency))
    assert order.is_paid(), "Order got paid"
    assert order.can_set_complete(), "Finalization is possible"
    order.status = OrderStatus.objects.get_default_complete()
    assert order.is_complete(), "Finalization done"

    summary = order.get_tax_summary()
    assert len(summary) == 2
    assert summary[0].tax_id is None
    assert summary[0].tax_code == ''
    assert summary[0].tax_amount == Money(0, currency)
    assert summary[0].tax_rate == 0
    assert summary[1].tax_rate * 100 == 50
    assert summary[1].based_on == Money(100, currency)
    assert summary[1].tax_amount == Money(50, currency)
    assert summary[1].taxful == summary[1].based_on + summary[1].tax_amount


@pytest.mark.django_db
def test_order_verification():
    product = get_default_product()
    supplier = get_default_supplier()
    order = create_order_with_product(product, supplier=supplier, quantity=3, n_lines=10, taxless_base_unit_price=10)
    order.require_verification = True
    order.save()
    assert not order.check_all_verified(), "Nothing is verified by default"
    order.lines.filter(pk=order.lines.filter(verified=False).first().pk).update(verified=True)
    assert not order.check_all_verified(), "All is not verified even if something is"
    order.lines.all().update(verified=True)
    assert order.check_all_verified(), "All is now verified"
    assert not order.require_verification, "Verification complete"


@pytest.mark.django_db
def test_empty_order():
    order = create_empty_order()
    order.save()
    with pytest.raises(NoProductsToShipException):
        order.create_shipment_of_all_products()
    with pytest.raises(NoProductsToShipException):
        order.create_shipment(supplier=None, product_quantities={1: 0})
    order.set_canceled()
    assert not order.can_set_complete(), "Can't process canceled order"
    order.set_canceled()  # Again! (This should be a no-op)
    order.delete()
    assert order.pk and order.deleted, "Order is soft-deleted"
    order.delete()  # Again! (This, too, should be a no-op)


@pytest.mark.django_db
def test_known_extra_data():
    order = create_empty_order()
    order.shipping_data = {"instruction": "Hello"}
    order.payment_data = {"ssn": "101010-010X"}
    order.extra_data = {"wrapping_color": "blue"}
    order.save()
    with override_settings(
        SHOOP_ORDER_KNOWN_SHIPPING_DATA_KEYS=[("instruction", "Instruction")],
        SHOOP_ORDER_KNOWN_PAYMENT_DATA_KEYS=[("ssn", "Social Security Number")],
        SHOOP_ORDER_KNOWN_EXTRA_DATA_KEYS=[("wrapping_color", "Wrapping Color")],
    ):
        known_data = dict(order.get_known_additional_data())
        assert ("Instruction" in known_data)
        assert ("Social Security Number" in known_data)
        assert ("Wrapping Color" in known_data)


@pytest.mark.django_db
def test_anon_disabling():
    with override_settings(SHOOP_ALLOW_ANONYMOUS_ORDERS=False):
        with pytest.raises(ValidationError):
            order = create_empty_order()
            order.save()
