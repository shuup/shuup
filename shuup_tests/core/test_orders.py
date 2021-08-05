# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
import six
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.utils.timezone import now

from shuup.core.excs import (
    InvalidRefundAmountException,
    NoPaymentToCreateException,
    NoProductsToShipException,
    RefundExceedsAmountException,
    RefundExceedsQuantityException,
    SupplierHasNoSupplierModules,
)
from shuup.core.models import (
    AnonymousContact,
    Order,
    OrderLine,
    OrderLineTax,
    OrderLineType,
    OrderStatus,
    PaymentStatus,
    ProductMedia,
    ProductMediaKind,
    ShipmentStatus,
    ShippingStatus,
)
from shuup.core.pricing import TaxfulPrice, TaxlessPrice, get_pricing_module
from shuup.testing.factories import (
    add_product_to_order,
    create_empty_order,
    create_order_with_product,
    create_product,
    get_address,
    get_default_product,
    get_default_shop,
    get_default_supplier,
    get_default_tax,
    get_initial_order_status,
    get_random_filer_image,
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
        status=get_initial_order_status(),
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
        OrderLine(product=get_default_product(), type=OrderLineType.OTHER).save()


@pytest.mark.django_db
def test_line_discount():
    order = create_empty_order(prices_include_tax=False)
    order.save()
    currency = order.shop.currency
    ol = OrderLine(order=order, type=OrderLineType.OTHER, quantity=5, text="Thing")
    ol.discount_amount = order.shop.create_price(50)
    ol.base_unit_price = order.shop.create_price(40)
    ol.save()
    order_line_tax = OrderLineTax.from_tax(get_default_tax(), ol.taxless_price.amount, order_line=ol)
    order_line_tax.save()
    ol.taxes.add(order_line_tax)
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
    order_line_tax = OrderLineTax.from_tax(get_default_tax(), ol.taxless_price.amount, order_line=ol)
    order_line_tax.save()
    ol.taxes.add(order_line_tax)
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
        product, supplier=supplier, quantity=PRODUCTS_TO_SEND, taxless_base_unit_price=10, tax_rate=Decimal("0.5")
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
    assert shipment.weight == product.gross_weight * PRODUCTS_TO_SEND, "Gravity works"
    assert not order.get_unshipped_products(), "Nothing was left in the warehouse"
    order.shipping_status = ShippingStatus.FULLY_SHIPPED
    order.create_payment(order.taxful_total_price)
    assert order.payments.exists(), "A payment was created"
    with pytest.raises(NoPaymentToCreateException):
        order.create_payment(Money(6, currency))
    assert order.is_paid(), "Order got paid"
    assert order.can_set_complete(), "Finalization is possible"
    order.change_status(next_status=OrderStatus.objects.get_default_complete(), save=False)
    assert order.is_complete(), "Finalization done"

    summary = order.get_tax_summary()
    assert len(summary) == 2
    assert summary[0].tax_rate * 100 == 50
    assert summary[0].based_on == Money(100, currency)
    assert summary[0].tax_amount == Money(50, currency)
    assert summary[0].taxful == summary[0].based_on + summary[0].tax_amount
    assert summary[1].tax_id is None
    assert summary[1].tax_code == ""
    assert summary[1].tax_amount == Money(0, currency)
    assert summary[1].tax_rate == 0
    assert order.get_total_tax_amount() == Money(50, currency)


@pytest.mark.django_db
def test_cannot_ship_basic_order_without_supplier_module():
    PRODUCTS_TO_SEND = 10
    product = get_default_product()
    supplier = get_default_supplier()
    supplier.supplier_modules.set([])
    supplier.stock_managed = False
    supplier.save()
    order = create_order_with_product(
        product, supplier=supplier, quantity=PRODUCTS_TO_SEND, taxless_base_unit_price=10, tax_rate=Decimal("0.5")
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
    with pytest.raises(SupplierHasNoSupplierModules):
        shipment = order.create_shipment_of_all_products(supplier=supplier)


@pytest.mark.django_db
@pytest.mark.parametrize("include_taxes", [True, False])
def test_complex_order_tax(include_taxes):
    tax = get_default_tax()
    quantities = [44, 23, 65]
    product = get_default_product()
    supplier = get_default_supplier()
    shop = get_default_shop()
    shop.prices_include_tax = include_taxes
    shop.save()

    order = create_empty_order(shop=shop)
    order.full_clean()
    order.save()

    pricing_context = get_pricing_module().get_context_from_data(
        shop=shop,
        customer=order.customer or AnonymousContact(),
    )

    total_price = Decimal("0")
    price = Decimal("50")

    for quantity in quantities:
        total_price += quantity * price
        add_product_to_order(order, supplier, product, quantity, price, tax.rate, pricing_context)
    order.cache_prices()
    order.save()

    currency = "EUR"
    summary = order.get_tax_summary()[0]

    assert summary.tax_rate == tax.rate
    assert summary.based_on == Money(total_price, currency)
    assert summary.tax_amount == Money(total_price * tax.rate, currency)
    assert summary.taxful == summary.based_on + summary.tax_amount
    assert order.get_total_tax_amount() == Money(total_price * tax.rate, currency)


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

    assert not order.get_available_shipping_methods()
    assert not order.get_available_shipping_methods()


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
        assert "Instruction" in known_data
        assert "Social Security Number" in known_data
        assert "Wrapping Color" in known_data


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
    taxless_base_unit_price = shop.create_price(200)
    order = create_order_with_product(product, supplier, 3, taxless_base_unit_price, tax_rate, shop=shop)
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

    order.create_refund([{"line": product_line, "quantity": 1, "amount": (product_line.taxful_price.amount / 3)}])
    assert len(order.lines.all()) == 2
    assert order.lines.last().ordering == 1
    assert order.has_refunds()

    # Confirm the value of the refund
    assert order.lines.last().taxful_price == -product_line.base_unit_price
    assert order.lines.last().tax_amount == -(product_line.taxless_base_unit_price * tax_rate).amount

    # Create a refund with a parent line and amount
    order.create_refund([{"line": product_line, "quantity": 1, "amount": product_line.taxful_price.amount / 3}])
    assert len(order.lines.all()) == 3
    assert order.lines.last().ordering == 2

    assert order.lines.last().taxful_price.amount == -taxless_base_unit_price.amount * (1 + tax_rate)
    assert order.lines.last().tax_amount == -taxless_base_unit_price.amount * tax_rate

    assert order.taxless_total_price.amount == taxless_base_unit_price.amount
    assert order.taxful_total_price.amount == taxless_base_unit_price.amount * (1 + tax_rate)
    assert order.can_create_refund()
    assert order.get_total_tax_amount() == Money(
        (order.taxful_total_price_value - order.taxless_total_price_value), order.currency
    )

    # Try to refunding remaining amount without a parent line
    with pytest.raises(AssertionError):
        order.create_refund([{"amount": taxless_base_unit_price}])

    # refund remaining amount
    order.create_refund([{"line": product_line, "quantity": 1, "amount": product_line.taxful_price.amount / 3}])
    assert len(order.lines.all()) == 4
    assert order.lines.last().ordering == 3
    assert order.lines.last().taxful_price.amount == -taxless_base_unit_price.amount * (1 + tax_rate)

    assert not order.taxful_total_price.amount
    assert not order.can_create_refund()
    assert order.get_total_tax_amount() == Money(
        (order.taxful_total_price_value - order.taxless_total_price_value), order.currency
    )

    with pytest.raises(RefundExceedsAmountException):
        order.create_refund([{"line": product_line, "quantity": 1, "amount": taxless_base_unit_price.amount}])


@pytest.mark.django_db
def test_refund_entire_order():
    shop = get_default_shop()
    supplier = get_simple_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=10,
    )
    supplier.adjust_stock(product.id, 5)
    check_stock_counts(supplier, product, 5, 5)

    order = create_order_with_product(product, supplier, 2, 200, Decimal("0.24"), shop=shop)
    order.cache_prices()

    original_total_price = order.taxful_total_price
    check_stock_counts(supplier, product, 5, 3)

    # Create a full refund with `restock_products` set to False
    order.create_full_refund(restock_products=False)

    # Confirm the refund was created with correct amount
    assert order.taxless_total_price.amount.value == 0
    assert order.taxful_total_price.amount.value == 0
    refund_line = order.lines.order_by("ordering").last()
    assert refund_line.type == OrderLineType.REFUND
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
    )
    supplier.adjust_stock(product.id, 5)
    check_stock_counts(supplier, product, 5, 5)

    order = create_order_with_product(product, supplier, 2, 200, shop=shop)
    order.cache_prices()

    check_stock_counts(supplier, product, 5, 3)

    # Create a full refund with `restock_products` set to True
    order.create_full_refund(restock_products=True)

    # restock logical count
    check_stock_counts(supplier, product, 5, 5)


@pytest.mark.django_db
@pytest.mark.parametrize("restock", [True, False])
def test_refund_with_shipment(restock):
    shop = get_default_shop()
    supplier = get_simple_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=10,
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

    # mark all shipments as sent
    order.shipments.update(status=ShipmentStatus.SENT)
    order.update_shipping_status()

    # still not shipped as there is unshipped products
    assert order.get_unshipped_products()
    assert order.shipping_status == ShippingStatus.PARTIALLY_SHIPPED

    # Check correct refunded quantities
    assert not product_line.refunded_quantity

    # Create a refund that refunds from unshipped quantity first, then shipped quantity, check stocks
    check_stock_counts(supplier, product, physical=8, logical=6)
    order.create_refund(
        [{"line": product_line, "quantity": 3, "amount": Money(600, order.currency), "restock_products": restock}]
    )
    assert product_line.refunded_quantity == 3

    # mark all shipments as sent
    order.shipments.update(status=ShipmentStatus.SENT)
    order.update_shipping_status()

    assert not order.get_unshipped_products()
    assert order.shipping_status == ShippingStatus.FULLY_SHIPPED
    if restock:
        check_stock_counts(supplier, product, physical=9, logical=9)
    else:
        check_stock_counts(supplier, product, physical=8, logical=6)

    # Create a second refund that refunds the last shipped quantity, check stocks
    order.create_refund(
        [{"line": product_line, "quantity": 1, "amount": Money(200, order.currency), "restock_products": restock}]
    )
    assert product_line.refunded_quantity == 4
    if restock:
        # Make sure we're not restocking more than maximum restockable quantity
        check_stock_counts(supplier, product, physical=10, logical=10)
    else:
        # Make sure maximum restockable quantity is not 0
        check_stock_counts(supplier, product, physical=8, logical=6)
    assert order.get_total_tax_amount() == Money(
        order.taxful_total_price_value - order.taxless_total_price_value, order.currency
    )


@pytest.mark.django_db
def test_cannot_refund_entire_order_restock_shipment_no_supplier_module():
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=10,
    )
    order = create_order_with_product(product, supplier, 2, 200, shop=shop)
    product_line = order.lines.first()
    order.create_shipment({product_line.product: 2}, supplier=supplier)

    supplier.supplier_modules.clear()
    # Create a full refund with `restock_products` set to True
    with pytest.raises(SupplierHasNoSupplierModules):
        order.create_full_refund(restock_products=True)


@pytest.mark.django_db
@pytest.mark.parametrize("restock", [True, False])
def test_refund_without_shipment(restock):
    shop = get_default_shop()
    supplier = get_simple_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=10,
    )
    # Start out with a supplier with quantity of 10 of a product
    supplier.adjust_stock(product.id, 10)
    check_stock_counts(supplier, product, physical=10, logical=10)

    order = create_order_with_product(product, supplier, 2, 200, shop=shop)
    order.cache_prices()
    check_stock_counts(supplier, product, physical=10, logical=8)

    # Restock value shouldn't matter if we don't have any shipments
    product_line = order.lines.first()
    order.create_refund(
        [{"line": product_line, "quantity": 2, "amount": Money(400, order.currency), "restock_products": restock}]
    )

    if restock:
        check_stock_counts(supplier, product, physical=10, logical=10)
    else:
        check_stock_counts(supplier, product, physical=10, logical=8)
    assert product_line.refunded_quantity == 2
    assert order.get_total_tax_amount() == Money(
        order.taxful_total_price_value - order.taxless_total_price_value, order.currency
    )


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
    order.cache_prices()
    assert len(order.lines.all()) == 1

    line = order.lines.first()
    assert line.max_refundable_amount == line.taxful_price.amount

    partial_refund_amount = Money(10, order.currency)
    assert partial_refund_amount.value > 0

    order.create_refund([{"line": line, "quantity": 1, "amount": partial_refund_amount}])
    assert line.max_refundable_amount == line.taxful_price.amount - partial_refund_amount
    assert order.get_total_tax_amount() == Money(
        order.taxful_total_price_value - order.taxless_total_price_value, order.currency
    )


@pytest.mark.django_db
def test_refunds_for_discounted_order_lines():
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=10,
    )

    order = create_order_with_product(product, supplier, 2, 200, shop=shop)
    discount_line = OrderLine(
        order_id=order.id, type=OrderLineType.DISCOUNT, quantity=1, discount_amount_value=Decimal("0.54321")
    )
    discount_line.save()
    order.lines.add(discount_line)

    # Lines without quantity shouldn't affect refunds
    other_line = OrderLine(
        order=order, type=OrderLineType.OTHER, text="This random line for textual information", quantity=0
    )
    other_line.save()
    order.lines.add(other_line)

    product_line = order.lines.filter(type=OrderLineType.PRODUCT).first()
    product_line.discount_amount = TaxfulPrice(100, order.currency)
    product_line.save()
    taxful_price_with_discount = product_line.taxful_price
    order.cache_prices()
    order.save()

    assert product_line.base_price == TaxfulPrice(400, order.currency)
    assert taxful_price_with_discount == TaxfulPrice(300, order.currency)

    # try to refund only the product line - should fail since this would result in a negative total
    with pytest.raises(RefundExceedsAmountException):
        order.create_refund([{"line": product_line, "quantity": 2, "amount": taxful_price_with_discount.amount}])

    # try to refund the product line with a negative amount
    with pytest.raises(InvalidRefundAmountException):
        order.create_refund([{"line": product_line, "quantity": 1, "amount": -taxful_price_with_discount.amount}])
    # try to refund the discount line with a positive amount
    with pytest.raises(InvalidRefundAmountException):
        order.create_refund([{"line": discount_line, "quantity": 1, "amount": -discount_line.taxful_price.amount}])

    order.create_refund(
        [
            {"line": discount_line, "quantity": 1, "amount": discount_line.taxful_price.amount},
            {"line": product_line, "quantity": 2, "amount": taxful_price_with_discount.amount},
        ]
    )
    assert product_line.max_refundable_amount.value == 0
    assert discount_line.max_refundable_amount.value == 0
    assert order.taxful_total_price.value == 0

    order = create_order_with_product(product, supplier, 2, 200, shop=shop)
    discount_line = OrderLine(
        order_id=order.id, type=OrderLineType.DISCOUNT, quantity=1, discount_amount_value=Decimal("0.54321")
    )
    discount_line.save()
    order.lines.add(discount_line)
    product_line = order.lines.filter(type=OrderLineType.PRODUCT).first()
    product_line.discount_amount = TaxfulPrice(100, order.currency)
    product_line.save()

    # Lines without quantity shouldn't affect refunds
    other_line = OrderLine(
        order=order, type=OrderLineType.OTHER, text="This random line for textual information", quantity=0
    )
    other_line.save()
    order.lines.add(other_line)

    order.cache_prices()
    order.save()

    order.create_full_refund(restock_products=False)
    assert order.taxful_total_price.value == 0


@pytest.mark.django_db
def test_refunds_rounding_multiple_partial_refund():
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=29.264,
    )
    order = create_order_with_product(product, supplier, 2, 29.264, shop=shop)
    order.cache_prices()
    assert len(order.lines.all()) == 1

    line = order.lines.first()
    order.create_refund([{"line": line, "quantity": 1, "amount": Money("29.26", order.currency)}])
    assert order.taxful_total_price == order.shop.create_price("29.27")
    order.create_refund([{"line": line, "quantity": 1, "amount": Money("29.27", order.currency)}])
    assert line.max_refundable_amount == Money("0", order.currency)
    assert order.taxful_total_price == order.shop.create_price(0)


@pytest.mark.django_db
@pytest.mark.parametrize("restock", [True, False])
def test_partial_refund_limits(restock):
    shop = get_default_shop()
    supplier = get_simple_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=10,
    )
    # Start out with a supplier with quantity of 10 of a product
    supplier.adjust_stock(product.id, 10)
    check_stock_counts(supplier, product, physical=10, logical=10)

    quantity = 2
    order = create_order_with_product(product, supplier, quantity, 200, shop=shop)
    order.cache_prices()
    check_stock_counts(supplier, product, physical=10, logical=8)

    # try creating more partial refunds than possible
    product_line = order.lines.first()

    def create_refund():
        order.create_refund(
            [{"line": product_line, "quantity": 1, "amount": Money(1, order.currency), "restock_products": restock}]
        )

    # create more refunds than available
    for index in range(quantity + 1):
        if index == quantity:
            with pytest.raises(RefundExceedsQuantityException):
                create_refund()
        else:
            create_refund()

    if restock:
        check_stock_counts(supplier, product, physical=10, logical=10)
    else:
        check_stock_counts(supplier, product, physical=10, logical=8)

    assert product_line.refunded_quantity == 2


@pytest.mark.django_db
def test_can_create_shipment():
    shop = get_default_shop()
    supplier = get_simple_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=10,
    )
    supplier.adjust_stock(product.id, 10)

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
    )

    order = create_order_with_product(product, supplier, 1, 200, shop=shop)
    assert order.can_create_payment()
    order.cache_prices()

    # Partially paid orders can create payments
    payment_amount = order.taxful_total_price.amount / 2
    order.create_payment(payment_amount)
    assert order.can_create_payment()

    # But fully paid orders can't
    remaining_amount = order.taxful_total_price.amount - payment_amount
    order.create_payment(remaining_amount)
    assert not order.can_create_payment()

    order = create_order_with_product(product, supplier, 1, 200, shop=shop)
    order.cache_prices()
    assert order.can_create_payment()

    # Canceled orders can't create payments
    order.set_canceled()
    assert not order.can_create_payment()

    order = create_order_with_product(product, supplier, 2, 200, shop=shop)
    order.cache_prices()
    assert order.can_create_payment()

    # Partially refunded orders can create payments
    order.create_refund(
        [{"line": order.lines.first(), "quantity": 1, "amount": Money(200, order.currency), "restock": False}]
    )
    assert order.can_create_payment()

    # But fully refunded orders can't
    order.create_refund(
        [{"line": order.lines.first(), "quantity": 1, "amount": Money(200, order.currency), "restock": False}]
    )
    assert not order.can_create_payment()


@pytest.mark.django_db
def test_can_create_refund():
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=10,
    )

    order = create_order_with_product(product, supplier, 2, 200, shop=shop)
    order.payment_status = PaymentStatus.DEFERRED
    order.cache_prices()
    assert order.can_create_payment()

    # Partially refunded orders can create refunds
    order.create_refund(
        [{"line": order.lines.first(), "quantity": 1, "amount": Money(200, order.currency), "restock": False}]
    )
    assert order.can_create_refund()

    # But fully refunded orders can't
    order.create_refund(
        [{"line": order.lines.first(), "quantity": 1, "amount": Money(200, order.currency), "restock": False}]
    )
    assert not order.can_create_refund()


def assert_defaultdict_values(default, **kwargs):
    for key, value in kwargs.items():
        assert default[key] == value


@pytest.mark.django_db
def test_product_summary():
    shop = get_default_shop()
    supplier = get_simple_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=10,
    )
    supplier.adjust_stock(product.id, 5)

    # Order with 2 unshipped, non-refunded items and a shipping cost
    order = create_order_with_product(product, supplier, 2, 200, shop=shop)
    order.cache_prices()
    product_line = order.lines.first()
    shipping_line = order.lines.create(type=OrderLineType.SHIPPING, base_unit_price_value=5, quantity=1)

    # Make sure no invalid entries and check product quantities
    product_summary = order.get_product_summary()
    assert all(product_summary.keys())
    summary = product_summary[product.id]
    assert_defaultdict_values(summary, ordered=2, shipped=0, refunded=0, unshipped=2)

    # Create a shipment for the other item, make sure status changes
    assert order.shipping_status == ShippingStatus.NOT_SHIPPED
    assert order.can_create_shipment()
    order.create_shipment(supplier=supplier, product_quantities={product: 1})
    assert order.shipping_status == ShippingStatus.NOT_SHIPPED

    # mark all shipments as sent
    order.shipments.update(status=ShipmentStatus.SENT)
    order.update_shipping_status()
    assert order.shipping_status == ShippingStatus.PARTIALLY_SHIPPED

    order.create_refund([{"line": shipping_line, "quantity": 1, "amount": Money(5, order.currency), "restock": False}])

    product_summary = order.get_product_summary()
    assert all(product_summary.keys())
    summary = product_summary[product.id]
    assert_defaultdict_values(summary, ordered=2, shipped=1, refunded=0, unshipped=1)

    # Create a refund for 2 items, we should get no negative values
    order.create_refund([{"line": product_line, "quantity": 2, "amount": Money(200, order.currency), "restock": False}])

    product_summary = order.get_product_summary()
    assert all(product_summary.keys())
    summary = product_summary[product.id]
    assert_defaultdict_values(summary, ordered=2, shipped=1, refunded=2, unshipped=0)


def add_product_image(product, purchased=False):
    media1 = ProductMedia.objects.create(
        product=product,
        kind=ProductMediaKind.IMAGE,
        file=get_random_filer_image(),
        enabled=True,
        public=True,
        purchased=purchased,
    )
    media2 = ProductMedia.objects.create(
        product=product,
        kind=ProductMediaKind.IMAGE,
        file=get_random_filer_image(),
        enabled=True,
        public=True,
        purchased=purchased,
    )
    product.primary_image = media1
    product.media.add(media2)
    product.save()
    return (media1, media2)


@pytest.mark.django_db
def test_product_purchasable_media():
    shop = get_default_shop()
    supplier = get_simple_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=10,
    )
    medias = add_product_image(product, True)
    supplier.adjust_stock(product.id, 5)

    # Order with 2 unshipped, non-refunded items and a shipping cost
    order = create_order_with_product(product, supplier, 2, 200, shop=shop)

    order.create_shipment_of_all_products(supplier=supplier)
    order.shipping_status = ShippingStatus.FULLY_SHIPPED
    order.create_payment(order.taxful_total_price)
    currency = order.currency
    assert order.payments.exists(), "A payment was created"
    with pytest.raises(NoPaymentToCreateException):
        order.create_payment(Money(6, currency))

    order.save()
    assert order.is_paid()
    assert order.get_purchased_attachments().count() == len(medias)
