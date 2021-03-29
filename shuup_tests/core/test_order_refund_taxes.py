# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import pytest
from collections import defaultdict
from decimal import Decimal

from shuup.core.defaults.order_statuses import create_default_order_statuses
from shuup.core.models import OrderLine, OrderLineType, Supplier
from shuup.core.order_creator import OrderCreator, OrderSource
from shuup.testing import factories
from shuup.utils.money import Money
from shuup.utils.numbers import bankers_round


def bround(value):
    return bankers_round(value, 2)


@pytest.mark.parametrize("include_tax", [True, False])
@pytest.mark.django_db
def test_order_full_refund_with_taxes(include_tax):
    tax_rate = Decimal(0.2)  # 20%
    product_price = 100
    discount_amount = 30
    random_line_price = 5

    shop = factories.get_shop(include_tax)
    source = OrderSource(shop)
    source.status = factories.get_initial_order_status()
    supplier = factories.get_default_supplier(shop)
    create_default_order_statuses()
    tax = factories.get_tax("sales-tax", "Sales Tax", tax_rate)
    factories.create_default_tax_rule(tax)

    product = factories.create_product("sku", shop=shop, supplier=supplier, default_price=product_price)

    line = source.add_line(
        line_id="product-line",
        type=OrderLineType.PRODUCT,
        product=product,
        supplier=supplier,
        quantity=1,
        shop=shop,
        base_unit_price=source.create_price(product_price),
    )
    discount_line = source.add_line(
        line_id="discount-line",
        type=OrderLineType.DISCOUNT,
        supplier=supplier,
        quantity=1,
        base_unit_price=source.create_price(0),
        discount_amount=source.create_price(discount_amount),
        parent_line_id=line.line_id,
    )
    raw_total_price = Decimal(product_price - discount_amount)
    total_taxful = bround(source.taxful_total_price.value)
    total_taxless = bround(source.taxless_total_price.value)
    if include_tax:
        assert total_taxful == bround(raw_total_price)
        assert total_taxless == bround(raw_total_price / (1 + tax_rate))
    else:
        assert total_taxful == bround(raw_total_price * (1 + tax_rate))
        assert total_taxless == bround(raw_total_price)

    # Lines without quantity shouldn't affect refunds
    other_line = source.add_line(
        text="This random line for textual information", line_id="other-line", type=OrderLineType.OTHER, quantity=0
    )
    # Lines with quantity again should be able to be refunded normally.
    other_line_with_quantity = source.add_line(
        line_id="other_line_with_quantity",
        type=OrderLineType.OTHER,
        text="Special service $5/h",
        quantity=1,
        base_unit_price=source.create_price(random_line_price),
    )

    raw_total_price = Decimal(product_price - discount_amount + random_line_price)
    total_taxful = bround(source.taxful_total_price.value)
    total_taxless = bround(source.taxless_total_price.value)
    if include_tax:
        assert total_taxful == bround(raw_total_price)
        assert total_taxless == bround(raw_total_price / (1 + tax_rate))
    else:
        assert total_taxful == bround(raw_total_price * (1 + tax_rate))
        assert total_taxless == bround(raw_total_price)

    creator = OrderCreator()
    order = creator.create_order(source)
    assert order.taxful_total_price.value == total_taxful
    assert order.taxless_total_price.value == total_taxless

    order.create_payment(order.taxful_total_price)
    assert order.is_paid()

    order.create_full_refund()
    assert order.taxful_total_price_value == 0

    for parent_order_line in order.lines.filter(parent_line__isnull=True):
        if parent_order_line.quantity == 0:
            assert not parent_order_line.child_lines.exists()
        else:
            refund_line = parent_order_line.child_lines.filter(type=OrderLineType.REFUND).first()
            assert refund_line
            assert parent_order_line.taxful_price.value == -refund_line.taxful_price.value
            assert parent_order_line.taxless_price.value == -refund_line.taxless_price.value
            assert parent_order_line.price.value == -refund_line.price.value


@pytest.mark.parametrize("include_tax", [True, False])
@pytest.mark.django_db
def test_order_partial_refund_with_taxes(include_tax):
    tax_rate = Decimal(0.2)  # 20%
    product_price = 100
    discount_amount = 30
    random_line_price = 5
    refunded_amount = 15

    shop = factories.get_shop(include_tax)
    source = OrderSource(shop)
    source.status = factories.get_initial_order_status()
    supplier = factories.get_default_supplier(shop)
    create_default_order_statuses()
    tax = factories.get_tax("sales-tax", "Sales Tax", tax_rate)
    factories.create_default_tax_rule(tax)

    product = factories.create_product("sku", shop=shop, supplier=supplier, default_price=product_price)

    line = source.add_line(
        line_id="product-line",
        type=OrderLineType.PRODUCT,
        product=product,
        supplier=supplier,
        quantity=1,
        shop=shop,
        base_unit_price=source.create_price(product_price),
    )
    discount_line = source.add_line(
        line_id="discount-line",
        type=OrderLineType.DISCOUNT,
        supplier=supplier,
        quantity=1,
        base_unit_price=source.create_price(0),
        discount_amount=source.create_price(discount_amount),
        parent_line_id=line.line_id,
    )
    raw_total_price = Decimal(product_price - discount_amount)
    total_taxful = bround(source.taxful_total_price.value)
    total_taxless = bround(source.taxless_total_price.value)
    if include_tax:
        assert total_taxful == bround(raw_total_price)
        assert total_taxless == bround(raw_total_price / (1 + tax_rate))
    else:
        assert total_taxful == bround(raw_total_price * (1 + tax_rate))
        assert total_taxless == bround(raw_total_price)

    creator = OrderCreator()
    order = creator.create_order(source)
    assert order.taxful_total_price.value == total_taxful
    assert order.taxless_total_price.value == total_taxless

    order.create_payment(order.taxful_total_price)
    assert order.is_paid()

    refund_data = [
        dict(
            amount=Money(refunded_amount, shop.currency),
            quantity=1,
            line=order.lines.products().first(),
        )
    ]
    order.create_refund(refund_data)

    total_taxful = bround(order.taxful_total_price.value)
    total_taxless = bround(order.taxless_total_price.value)
    taxless_refunded_amount = refunded_amount / (1 + tax_rate)

    if include_tax:
        raw_total_price = Decimal(product_price - discount_amount - refunded_amount)
        assert total_taxful == bround(raw_total_price)
        assert total_taxless == bround(raw_total_price / (1 + tax_rate))
    else:
        # the refunded amount it considered a taxful price internally
        raw_total_price = Decimal(product_price - discount_amount)
        assert total_taxful == bround((raw_total_price * (1 + tax_rate)) - refunded_amount)
        assert total_taxless == bround(raw_total_price - taxless_refunded_amount)

    refund_line = order.lines.refunds().filter(type=OrderLineType.REFUND).first()
    if include_tax:
        assert refund_line.taxful_price.value == -bround(refunded_amount)
        assert refund_line.taxless_price.value == -bround(taxless_refunded_amount)
    else:
        assert refund_line.taxful_price.value == -bround(refunded_amount)
        assert refund_line.taxless_price.value == -bround(taxless_refunded_amount)
