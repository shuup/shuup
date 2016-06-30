# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from decimal import Decimal

import pytest
import six
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.utils.timezone import now

from shuup.core.excs import (
    NoPaymentToCreateException, NoProductsToShipException,
    RefundExceedsAmountException
)
from shuup.core.models import (
    Order, OrderLine, OrderLineTax, OrderLineType, OrderStatus,
    PaymentStatus, ShippingStatus, StockBehavior
)
from shuup.core.pricing import TaxfulPrice, TaxlessPrice
from shuup.testing.factories import (
    create_empty_order, create_order_with_product, create_product, get_address,
    get_default_product, get_default_shop, get_default_supplier,
    get_default_tax, get_initial_order_status
)
from shuup.utils.money import Money
from shuup_tests.simple_supplier.utils import get_simple_supplier


@pytest.mark.django_db
@pytest.mark.parametrize("save", (False, True))
def test_order_address_immutability_unsaved_address(save):
    billing_address = get_address()
    if save:
        billing_address.save()
    order = Order(
        shop=get_default_shop(),
        billing_address=billing_address.to_immutable(),
        order_date=now(),
        status=get_initial_order_status()
    )
    order.save()
    order.billing_address.name = "Mute Doge"
    with pytest.raises(ValidationError):
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
        get_default_tax(), ol.taxless_price.amount, order_line=ol))
    assert ol.taxless_discount_amount == order.shop.create_price(50)
    assert ol.taxful_discount_amount == TaxfulPrice(75, currency)
    assert ol.taxless_price == order.shop.create_price(150)
    assert ol.taxful_price == TaxfulPrice(150 + 75, currency)
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
    assert ol.taxless_price == TaxlessPrice(5 * 30 - 50, currency)
    ol.taxes.add(OrderLineTax.from_tax(
        get_default_tax(), ol.taxless_price.amount, order_line=ol))
    assert ol.taxless_discount_amount == TaxlessPrice(50, currency)
    assert ol.taxful_discount_amount == TaxfulPrice(75, currency)
    assert ol.taxless_price == TaxlessPrice(100, currency)
    assert ol.taxful_price == TaxfulPrice(150, currency)
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
    assert discount_order_line.price == price(-30)
    discount_order_line.save()

    order.cache_prices()
    order.check_all_verified()
    order.save()
    assert order.taxful_total_price == TaxfulPrice(PRODUCTS_TO_SEND * (10 + 5) - 30, currency)
    shipment = order.create_shipment_of_all_products(supplier=supplier)
    assert shipment.total_products == PRODUCTS_TO_SEND, "All products were shipped"
    assert shipment.weight == product.gross_weight * PRODUCTS_TO_SEND / 1000, "Gravity works"
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
    assert summary[0].tax_rate * 100 == 50
    assert summary[0].based_on == Money(100, currency)
    assert summary[0].tax_amount == Money(50, currency)
    assert summary[0].taxful == summary[0].based_on + summary[0].tax_amount
    assert summary[1].tax_id is None
    assert summary[1].tax_code == ''
    assert summary[1].tax_amount == Money(0, currency)
    assert summary[1].tax_rate == 0


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
    assert order.can_edit()
    order.set_canceled()
    assert not order.can_edit(), "Can't edit canceled order"
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
        SHUUP_ORDER_KNOWN_SHIPPING_DATA_KEYS=[("instruction", "Instruction")],
        SHUUP_ORDER_KNOWN_PAYMENT_DATA_KEYS=[("ssn", "Social Security Number")],
        SHUUP_ORDER_KNOWN_EXTRA_DATA_KEYS=[("wrapping_color", "Wrapping Color")],
    ):
        known_data = dict(order.get_known_additional_data())
        assert ("Instruction" in known_data)
        assert ("Social Security Number" in known_data)
        assert ("Wrapping Color" in known_data)


@pytest.mark.django_db
def test_anon_disabling():
    with override_settings(SHUUP_ALLOW_ANONYMOUS_ORDERS=False):
        with pytest.raises(ValidationError):
            order = create_empty_order()
            order.save()


@pytest.mark.django_db
def test_payments():
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product("test-sku", shop=get_default_shop(), default_price=10)
    order = create_order_with_product(product, supplier, 1, 200, shop=shop)
    order.cache_prices()

    assert order.get_total_paid_amount().value == 0
    assert order.get_total_unpaid_amount().value == order.taxful_total_price.value

    assert order.payment_status == PaymentStatus.NOT_PAID
    assert order.can_edit()

    partial_payment_amount = order.taxful_total_price / 2
    remaining_amount = order.taxful_total_price - partial_payment_amount
    order.create_payment(partial_payment_amount)
    assert order.payment_status == PaymentStatus.PARTIALLY_PAID
    assert not order.can_edit()

    order.create_payment(remaining_amount)
    assert order.payment_status == PaymentStatus.FULLY_PAID
    assert not order.can_edit()

@pytest.mark.django_db
def test_refunds():
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=10,
    )
    order = create_order_with_product(product, supplier, 2, 200, shop=shop)
    order.cache_prices()

    assert order.get_total_refunded_amount().value == 0
    assert order.get_total_unrefunded_amount().value == order.taxful_total_price.value
    assert order.can_edit()

    assert len(order.lines.all()) == 1

    product_line = order.lines.first()
    assert product_line.ordering == 0
    assert order.can_create_refund()
    assert not order.has_refunds()

    # Create a refund with a parent line and quantity
    order.create_refund([{"line": product_line, "quantity": 1}])
    assert len(order.lines.all()) == 2
    assert order.lines.last().ordering == 1
    assert order.has_refunds()

    # Confirm the value of the refund
    assert order.lines.last().taxful_price == -product_line.base_unit_price

    partial_refund_amount = order.taxful_total_price.amount / 2
    remaining_amount = order.taxful_total_price.amount - partial_refund_amount

    # Create a refund with a parent line and amount
    order.create_refund([{"line": product_line, "amount": partial_refund_amount}])
    assert len(order.lines.all()) == 3
    assert order.lines.last().ordering == 2

    assert order.lines.last().taxful_price.amount == -partial_refund_amount
    assert order.taxful_total_price.amount == remaining_amount
    assert order.can_create_refund()

    # Create a refund without parent line and remaining amount in order
    order.create_refund([{"amount": remaining_amount}])
    assert len(order.lines.all()) == 4
    assert order.lines.last().ordering == 3
    assert order.lines.last().taxful_price.amount == -remaining_amount

    assert not order.taxful_total_price.amount
    assert not order.can_create_refund()

    with pytest.raises(RefundExceedsAmountException):
        order.create_refund([{"amount": remaining_amount}])

@pytest.mark.django_db
def test_refund_entire_order():
    shop = get_default_shop()
    supplier = get_simple_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=10,
        stock_behavior=StockBehavior.STOCKED
    )
    supplier.adjust_stock(product.id, 5)
    assert supplier.get_stock_statuses([product.id])[product.id].logical_count == 5

    order = create_order_with_product(product, supplier, 2, 200, shop=shop)
    order.cache_prices()
    original_total_price = order.taxful_total_price

    assert supplier.get_stock_statuses([product.id])[product.id].logical_count == 3

    # Create a full refund with `restock_products` set to False
    order.create_full_refund(restock_products=False)

    # Confirm the refund was created with correct amount
    assert order.taxful_total_price.amount.value == 0
    refund_line = order.lines.order_by("ordering").last()
    assert refund_line.type == OrderLineType.REFUND
    assert refund_line.taxful_price == -original_total_price

    # Make sure stock status didn't change
    assert supplier.get_stock_statuses([product.id])[product.id].logical_count == 3

    # Delete refund line
    refund_line.delete()
    order.cache_prices()

    assert order.taxful_total_price == original_total_price

    # Create a full refund with `restock_products` set to True
    order.create_full_refund(restock_products=True)

    # Make sure product was restocked
    assert supplier.get_stock_statuses([product.id])[product.id].logical_count == 5


@pytest.mark.django_db
def test_refund_with_product_restock():
    shop = get_default_shop()
    supplier = get_simple_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=10,
        stock_behavior=StockBehavior.STOCKED
    )
    supplier.adjust_stock(product.id, 5)
    assert supplier.get_stock_statuses([product.id])[product.id].logical_count == 5

    order = create_order_with_product(product, supplier, 2, 200, shop=shop)
    order.cache_prices()

    assert supplier.get_stock_statuses([product.id])[product.id].logical_count == 3

    # Create a refund with a parent line and quanity with `restock_products` set to False
    product_line = order.lines.first()
    order.create_refund([{"line": product_line, "quantity": 1, "restock_products": False}])

    assert supplier.get_stock_statuses([product.id])[product.id].logical_count == 3
    assert order.lines.last().taxful_price == -product_line.base_unit_price
    assert order.get_total_unrefunded_amount() == product_line.base_unit_price.amount

    # Create a refund with a parent line and quanity with `restock_products` set to True
    product_line = order.lines.first()
    order.create_refund([{"line": product_line, "quantity": 1, "restock_products": True}])

    assert supplier.get_stock_statuses([product.id])[product.id].logical_count == 4
    assert not order.taxful_total_price


@pytest.mark.django_db
def test_max_refundable_amount():
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=10,
    )
    order = create_order_with_product(product, supplier, 2, 200, shop=shop)

    assert len(order.lines.all()) == 1

    line = order.lines.first()
    assert line.max_refundable_amount == line.taxful_price.amount

    partial_refund_amount = Money(10, order.currency)
    assert partial_refund_amount.value > 0

    order.create_refund([{"line": line, "amount": partial_refund_amount}])
    assert line.max_refundable_amount == line.taxful_price.amount - partial_refund_amount


@pytest.mark.django_db
def test_refunds_for_discounted_order_lines():
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=10,
        stock_behavior=StockBehavior.STOCKED
    )

    order = create_order_with_product(product, supplier, 2, 200, shop=shop)
    order.cache_prices()

    product_line = order.lines.first()
    product_line.discount_amount = TaxfulPrice(100, order.currency)
    taxful_price_with_discount = product_line.taxful_price
    assert product_line.base_price == TaxfulPrice(400, order.currency)
    assert taxful_price_with_discount == TaxfulPrice(300, order.currency)

    order.create_refund([{"line": product_line, "quantity": 1}])
    assert order.lines.refunds().first().taxful_price == (-taxful_price_with_discount / 2)


@pytest.mark.django_db
def test_refunds_with_quantities():
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=10,
        stock_behavior=StockBehavior.STOCKED
    )

    order = create_order_with_product(product, supplier, 3, 200, shop=shop)
    order.cache_prices()
    assert not order.lines.refunds()

    product_line = order.lines.first()
    refund_amount = Money(100, order.currency)
    order.create_refund([{"line": product_line, "quantity": 2, "amount": refund_amount}])
    assert len(order.lines.refunds()) == 2

    quantity_line = order.lines.refunds().filter(quantity=2).first()
    assert quantity_line
    amount_line = order.lines.refunds().filter(quantity=1).first()
    assert amount_line

    assert quantity_line.taxful_base_unit_price == -product_line.taxful_base_unit_price
    assert amount_line.taxful_price.amount == -refund_amount
