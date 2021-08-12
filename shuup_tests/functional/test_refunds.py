# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import decimal
import pytest

from shuup.campaigns.models.basket_conditions import BasketTotalProductAmountCondition
from shuup.campaigns.models.basket_effects import BasketDiscountAmount
from shuup.campaigns.models.campaigns import BasketCampaign, CatalogCampaign
from shuup.campaigns.models.catalog_filters import CategoryFilter
from shuup.campaigns.models.product_effects import ProductDiscountAmount
from shuup.core.models import AnonymousContact, OrderLineType, PaymentStatus, ShipmentStatus, ShippingStatus
from shuup.core.order_creator import OrderCreator
from shuup.core.pricing import get_pricing_module
from shuup.testing.factories import (
    create_default_tax_rule,
    create_product,
    get_default_category,
    get_default_tax_class,
    get_initial_order_status,
    get_shop,
    get_tax,
)
from shuup.utils.money import Money
from shuup_tests.simple_supplier.utils import get_simple_supplier
from shuup_tests.utils.basketish_order_source import BasketishOrderSource

INITIAL_PRODUCT_QUANTITY = 10


def check_stock_counts(supplier, product, physical, logical):
    physical_count = supplier.get_stock_statuses([product.id])[product.id].physical_count
    logical_count = supplier.get_stock_statuses([product.id])[product.id].logical_count
    assert physical_count == physical
    assert logical_count == logical


def _get_product_data():
    return [
        {"sku": "sku1234", "default_price": decimal.Decimal("14.756"), "quantity": decimal.Decimal("1")},
        {"sku": "sku12345", "default_price": decimal.Decimal("10"), "quantity": decimal.Decimal("2")},
        {"sku": "sku123456", "default_price": decimal.Decimal("14.756"), "quantity": decimal.Decimal("2")},
    ]


def _get_other_line_data():
    return [
        {
            "type": OrderLineType.SHIPPING,
            "quantity": 1,
            "text": "shipping",
            "base_unit_price_value": decimal.Decimal("10"),
        },
        {
            "type": OrderLineType.PAYMENT,
            "quantity": 1,
            "text": "payment",
            "base_unit_price_value": decimal.Decimal("10"),
        },
    ]


def _add_basket_campaign(shop):
    campaign = BasketCampaign.objects.create(shop=shop, name="test", public_name="test", active=True)
    BasketDiscountAmount.objects.create(discount_amount=shop.create_price("10"), campaign=campaign)
    rule = BasketTotalProductAmountCondition.objects.create(value=1)
    campaign.conditions.add(rule)
    campaign.save()


def _add_catalog_campaign(shop):
    campaign = CatalogCampaign.objects.create(shop=shop, name="test", public_name="test", active=True)
    category_filter = CategoryFilter.objects.create()
    category_filter.categories.add(get_default_category())
    category_filter.save()
    ProductDiscountAmount.objects.create(campaign=campaign, discount_amount=5)


def _add_taxes():
    tax = get_tax(code=u"test_code", name=u"default", rate=0.24)
    tax2 = get_tax(code=u"test_code2", name=u"default", rate=0.11)
    create_default_tax_rule(tax)
    create_default_tax_rule(tax2)


def _get_order(prices_include_tax=False, include_basket_campaign=False, include_catalog_campaign=False):
    shop = get_shop(prices_include_tax=prices_include_tax)
    supplier = get_simple_supplier(shop=shop)

    if include_basket_campaign:
        _add_basket_campaign(shop)

    if include_catalog_campaign:
        _add_catalog_campaign(shop)
    _add_taxes()

    source = BasketishOrderSource(shop)
    source.status = get_initial_order_status()
    ctx = get_pricing_module().get_context_from_data(shop, AnonymousContact())
    for product_data in _get_product_data():
        quantity = product_data.pop("quantity")
        product = create_product(
            sku=product_data.pop("sku"), shop=shop, supplier=supplier, tax_class=get_default_tax_class(), **product_data
        )
        shop_product = product.get_shop_instance(shop)
        shop_product.categories.add(get_default_category())
        shop_product.save()
        supplier.adjust_stock(product.id, INITIAL_PRODUCT_QUANTITY)
        pi = product.get_price_info(ctx)
        source.add_line(
            type=OrderLineType.PRODUCT,
            product=product,
            supplier=supplier,
            quantity=quantity,
            base_unit_price=pi.base_unit_price,
            discount_amount=pi.discount_amount,
        )
    oc = OrderCreator()
    order = oc.create_order(source)
    order.create_payment(Money("1", "EUR"))
    assert not order.has_refunds()
    assert order.can_create_refund()
    assert order.shipping_status == ShippingStatus.NOT_SHIPPED
    assert order.payment_status == PaymentStatus.PARTIALLY_PAID
    return order


@pytest.mark.django_db
@pytest.mark.parametrize("prices_include_tax", (True, False))
def test_create_full_refund(prices_include_tax):
    order = _get_order(prices_include_tax, True, True)
    supplier = get_simple_supplier(order.shop)
    original_order_total = order.taxful_total_price
    num_order_lines = order.lines.count()
    order.create_full_refund(restock_products=True)

    for line in order.lines.products():
        check_stock_counts(supplier, line.product, INITIAL_PRODUCT_QUANTITY, INITIAL_PRODUCT_QUANTITY)

    assert order.has_refunds()
    assert not order.can_create_refund()
    assert not order.taxful_total_price_value
    assert not order.taxless_total_price_value
    assert order.lines.refunds().count() == num_order_lines

    assert order.shipping_status == ShippingStatus.NOT_SHIPPED
    assert order.payment_status == PaymentStatus.FULLY_PAID
    assert order.get_total_refunded_amount() == original_order_total.amount
    assert not order.get_total_unrefunded_amount().value
    assert not order.get_total_unrefunded_quantity()


@pytest.mark.django_db
@pytest.mark.parametrize("prices_include_tax", (True, False))
def test_create_refund_line_by_line(prices_include_tax):
    supplier = get_simple_supplier()
    order = _get_order(prices_include_tax, True, True)

    for line in order.lines.products():
        check_stock_counts(supplier, line.product, INITIAL_PRODUCT_QUANTITY, INITIAL_PRODUCT_QUANTITY - line.quantity)

    original_order_total = order.taxful_total_price
    num_order_lines = order.lines.count()

    # refund the discount lines first
    for line in order.lines.discounts():
        order.create_refund([{"line": line, "quantity": line.quantity, "amount": line.taxful_price.amount}])

    # refund each line 1 by 1
    for line in order.lines.products():
        order.create_refund(
            [{"line": line, "quantity": line.quantity, "amount": line.taxful_price.amount, "restock_products": True}]
        )

    for line in order.lines.products():
        check_stock_counts(supplier, line.product, INITIAL_PRODUCT_QUANTITY, INITIAL_PRODUCT_QUANTITY)

    assert order.has_refunds()
    assert not order.can_create_refund()
    assert not order.taxful_total_price_value
    assert not order.taxless_total_price_value
    assert order.lines.refunds().count() == num_order_lines
    assert order.shipping_status == ShippingStatus.NOT_SHIPPED
    assert order.get_total_refunded_amount() == original_order_total.amount
    assert not order.get_total_unrefunded_amount().value


@pytest.mark.django_db
@pytest.mark.parametrize("prices_include_tax", (True, False))
def test_create_refund_amount(prices_include_tax):
    supplier = get_simple_supplier()
    order = _get_order(prices_include_tax, True, True)

    original_order_total = order.taxful_total_price
    num_order_lines = order.lines.count()

    # refund the discount lines first
    for line in order.lines.discounts():
        order.create_refund([{"line": "amount", "quantity": line.quantity, "amount": line.taxful_price.amount}])

    # refund each line 1 by 1
    for line in order.lines.products():
        order.create_refund(
            [{"line": "amount", "quantity": 1, "amount": line.taxful_price.amount, "restock_products": True}]
        )

    assert order.has_refunds()
    # assert not order.can_create_refund()
    assert not order.taxful_total_price_value
    assert not order.taxless_total_price_value
    assert order.lines.refunds().count() == num_order_lines
    assert order.shipping_status == ShippingStatus.NOT_SHIPPED
    assert order.payment_status == PaymentStatus.FULLY_PAID
    assert order.get_total_refunded_amount() == original_order_total.amount
    assert not order.get_total_unrefunded_amount().value

    for line in order.lines.products():
        order.create_refund(
            [{"line": line, "quantity": line.quantity, "amount": Money(0, "EUR"), "restock_products": True}]
        )

    # nothing changes
    assert order.shipping_status == ShippingStatus.NOT_SHIPPED
