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
    get_default_tax, get_initial_order_status, get_shipping_method
)
from shuup.utils.money import Money
from shuup_tests.simple_supplier.utils import get_simple_supplier


def check_stock_counts(supplier, product, physical, logical):
    physical_count = supplier.get_stock_statuses([product.id])[product.id].physical_count
    logical_count = supplier.get_stock_statuses([product.id])[product.id].logical_count
    assert physical_count == physical
    assert logical_count == logical


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
    tax_rate = Decimal("0.1")
    order = create_order_with_product(product, supplier, 2, 200, tax_rate, shop=shop)
    order.payment_status = PaymentStatus.DEFERRED
    order.cache_prices()
    order.save()

    assert order.get_total_refunded_amount().value == 0
    assert order.get_total_unrefunded_amount().value == order.taxful_total_price.value
    assert not order.can_edit()

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
    assert order.lines.last().tax_amount == -(product_line.base_unit_price * tax_rate).amount

    partial_refund_amount = order.taxful_total_price.amount / 2
    remaining_amount = order.taxful_total_price.amount - partial_refund_amount

    # Create a refund with a parent line and amount
    order.create_refund([{"line": product_line, "amount": partial_refund_amount}])
    assert len(order.lines.all()) == 3
    assert order.lines.last().ordering == 2

    assert order.lines.last().taxful_price.amount == -partial_refund_amount
    assert order.lines.last().tax_amount == -partial_refund_amount * tax_rate

    assert order.taxless_total_price.amount == remaining_amount * (1 - tax_rate)
    assert order.taxful_total_price.amount == remaining_amount
    assert order.can_create_refund()

    # Try to refunding remaining amount without a parent line
    with pytest.raises(AssertionError):
        order.create_refund([{"amount": remaining_amount}])

    # refund remaining amount
    order.create_refund([{"line": product_line, "amount": remaining_amount}])
    assert len(order.lines.all()) == 4
    assert order.lines.last().ordering == 3
    assert order.lines.last().taxful_price.amount == -remaining_amount

    assert not order.taxful_total_price.amount
    assert not order.can_create_refund()

    with pytest.raises(RefundExceedsAmountException):
        order.create_refund([{"line": product_line, "amount": remaining_amount}])


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
    check_stock_counts(supplier, product, 5, 5)

    order = create_order_with_product(product, supplier, 2, 200, Decimal("0.1"), shop=shop)
    order.cache_prices()
    original_total_price = order.taxful_total_price
    check_stock_counts(supplier, product, 5, 3)

    # Create a full refund with `restock_products` set to False
    order.create_full_refund(restock_products=False)

    # Confirm the refund was created with correct amount
    assert order.taxless_total_price.amount.value == 0
    assert order.taxful_total_price.amount.value == 0
    refund_line = order.lines.order_by("ordering").last()
    assert refund_line.type == OrderLineType.QUANTITY_REFUND
    assert refund_line.taxful_price == -original_total_price

    # Make sure logical count reflects refunded products
    check_stock_counts(supplier, product, 5, 3)


@pytest.mark.django_db
def test_refund_entire_order_with_product_restock():
    shop = get_default_shop()
    supplier = get_simple_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=10,
        stock_behavior=StockBehavior.STOCKED
    )
    supplier.adjust_stock(product.id, 5)
    check_stock_counts(supplier, product, 5, 5)

    order = create_order_with_product(product, supplier, 2, 200, shop=shop)
    order.cache_prices()
    original_total_price = order.taxful_total_price

    check_stock_counts(supplier, product, 5, 3)

    # Create a full refund with `restock_products` set to True
    order.create_full_refund(restock_products=True)

    # Since no shipments were created, restocking is not possible
    check_stock_counts(supplier, product, 5, 3)



@pytest.mark.django_db
@pytest.mark.parametrize("restock", [True, False])
def test_refund_with_shipment(restock):
    shop = get_default_shop()
    supplier = get_simple_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=10,
        stock_behavior=StockBehavior.STOCKED
    )
    # Start out with a supplier with quantity of 10 of a product
    supplier.adjust_stock(product.id, 10)
    check_stock_counts(supplier, product, physical=10, logical=10)

    # Order 4 products, make sure product counts are accurate
    order = create_order_with_product(product, supplier, 4, 200, shop=shop)
    order.cache_prices()
    check_stock_counts(supplier, product, physical=10, logical=6)
    product_line = order.lines.first()

    # Shipment should decrease physical count by 2, logical by none
    order.create_shipment({product_line.product: 2}, supplier=supplier)
    check_stock_counts(supplier, product, physical=8, logical=6)
    assert order.shipping_status ==  ShippingStatus.PARTIALLY_SHIPPED

    # Check correct refunded quantities
    assert not product_line.refunded_quantity

    # Create a refund greater than restockable quantity, check stocks
    check_stock_counts(supplier, product, physical=8, logical=6)
    order.create_refund([{"line": product_line, "quantity": 3, "restock_products": restock}])
    assert product_line.refunded_quantity == 3
    assert order.shipping_status == ShippingStatus.FULLY_SHIPPED
    if restock:
        check_stock_counts(supplier, product, physical=10, logical=8)
    else:
        check_stock_counts(supplier, product, physical=8, logical=6)

    # Create a second refund greater than restockable quantity, check stocks
    order.create_refund([{"line": product_line, "quantity": 1, "restock_products": restock}])
    assert product_line.refunded_quantity == 4
    if restock:
        # Make sure we're not restocking more than maximum restockable quantity
        check_stock_counts(supplier, product, physical=10, logical=8)
    else:
        # Make sure maximum restockable quantity is not 0
        check_stock_counts(supplier, product, physical=8, logical=6)


@pytest.mark.django_db
@pytest.mark.parametrize("restock", [True, False])
def test_refund_without_shipment(restock):
    shop = get_default_shop()
    supplier = get_simple_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=10,
        stock_behavior=StockBehavior.STOCKED
    )
    # Start out with a supplier with quantity of 10 of a product
    supplier.adjust_stock(product.id, 10)
    check_stock_counts(supplier, product, physical=10, logical=10)

    order = create_order_with_product(product, supplier, 2, 200, shop=shop)
    order.cache_prices()
    check_stock_counts(supplier, product, physical=10, logical=8)

    # Restock value shouldn't matter if we don't have any shipments
    product_line = order.lines.first()
    order.create_refund([{"line": product_line, "quantity": 2, "restock_products": restock}])

    check_stock_counts(supplier, product, physical=10, logical=8)

    assert product_line.refunded_quantity == 2


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
    assert order.lines.refunds().count() == 2

    quantity_line = order.lines.refunds().filter(quantity=2).first()
    assert quantity_line
    amount_line = order.lines.refunds().filter(quantity=1).first()
    assert amount_line

    assert quantity_line.taxful_base_unit_price == -product_line.taxful_base_unit_price
    assert amount_line.taxful_price.amount == -refund_amount

@pytest.mark.django_db
def test_can_create_shipment():
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=10,
        stock_behavior=StockBehavior.STOCKED
    )

    order = create_order_with_product(product, supplier, 1, 200, shop=shop)
    assert order.can_create_shipment()

    # Fully shipped orders can't create shipments
    order.create_shipment_of_all_products(supplier)
    assert not order.can_create_shipment()

    order = create_order_with_product(product, supplier, 1, 200, shop=shop)
    assert order.can_create_shipment()

    # Canceled orders can't create shipments
    order.set_canceled()
    assert not order.can_create_shipment()


@pytest.mark.django_db
def test_can_create_payment():
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=10,
        stock_behavior=StockBehavior.STOCKED
    )

    order = create_order_with_product(product, supplier, 1, 200, shop=shop)
    assert order.can_create_payment()
    order.cache_prices()

    # Partially paid orders can create payments
    payment_amount = (order.taxful_total_price.amount / 2)
    order.create_payment(payment_amount)
    assert order.can_create_payment()

    # But fully paid orders can't
    remaining_amount = order.taxful_total_price.amount - payment_amount
    order.create_payment(remaining_amount)
    assert not order.can_create_payment()

    order = create_order_with_product(product, supplier, 1, 200, shop=shop)
    assert order.can_create_payment()

    # Canceled orders can't create payments
    order.set_canceled()
    assert not order.can_create_payment()

    order = create_order_with_product(product, supplier, 2, 200, shop=shop)
    assert order.can_create_payment()

    # Partially refunded orders can create payments
    order.create_refund([{"line": order.lines.first(), "quantity": 1, "restock": False}])
    assert order.can_create_payment()

    # But fully refunded orders can't
    order.create_refund([{"line": order.lines.first(), "quantity": 1, "restock": False}])
    assert not order.can_create_payment()


@pytest.mark.django_db
def test_can_create_refund():
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=10,
        stock_behavior=StockBehavior.STOCKED
    )

    order = create_order_with_product(product, supplier, 2, 200, shop=shop)
    assert order.can_create_payment()

    # Partially refunded orders can create refunds
    order.create_refund([{"line": order.lines.first(), "quantity": 1, "restock": False}])
    assert order.can_create_refund()

    # But fully refunded orders can't
    order.create_refund([{"line": order.lines.first(), "quantity": 1, "restock": False}])
    assert not order.can_create_refund()


def assert_defaultdict_values(default, **kwargs):
    for key, value in kwargs.items():
        assert default[key] == value


@pytest.mark.django_db
def test_product_summary():
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=10,
        stock_behavior=StockBehavior.STOCKED
    )

    # Order with 2 unshipped, non-refunded items and a shipping cost
    order = create_order_with_product(product, supplier, 2, 200, shop=shop)
    product_line = order.lines.first()
    sm = get_shipping_method(name="test", price=10)
    shipping_line  = order.lines.create(type=OrderLineType.SHIPPING, base_unit_price_value=5, quantity=1)

    # Make sure no invalid entries and check product quantities
    product_summary = order.get_product_summary()
    assert all(product_summary.keys())
    summary = product_summary[product.id]
    assert_defaultdict_values(summary, ordered=2, shipped=0, refunded=0, unshipped=2)

    # Create a shipment for the other item, make sure status changes
    assert order.shipping_status == ShippingStatus.NOT_SHIPPED
    assert order.can_create_shipment()
    order.create_shipment(supplier=supplier, product_quantities={product: 1})
    assert order.shipping_status == ShippingStatus.PARTIALLY_SHIPPED

    order.create_refund([{"line": shipping_line, "quantity": 1, "restock": False}])

    product_summary = order.get_product_summary()
    assert all(product_summary.keys())
    summary = product_summary[product.id]
    assert_defaultdict_values(summary, ordered=2, shipped=1, refunded=0, unshipped=1)

    # Create a refund for 2 items, we should get no negative values
    order.create_refund([{"line": product_line, "quantity": 2, "restock": False}])

    product_summary = order.get_product_summary()
    assert all(product_summary.keys())
    summary = product_summary[product.id]
    assert_defaultdict_values(summary, ordered=2, shipped=1, refunded=2, unshipped=0)
