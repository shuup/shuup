# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from decimal import Decimal

from shuup.core.models import OrderLine, OrderLineType, Shop, ShopStatus
from shuup.testing.factories import (
    add_product_to_order,
    create_empty_order,
    create_product,
    get_default_shop,
    get_default_supplier,
)
from shuup.utils.numbers import bankers_round
from shuup_tests.utils.basketish_order_source import BasketishOrderSource

PRICE_SPEC = [
    ([1, 2, 3, 4]),
    ([1, 2, 3, 6]),
    ([1, 2, 3, 8]),
    ([1.23223, 12.24442, 42.26233]),
    ([1223.46636, 13.24655, 411.234554]),
    ([101.74363, 12.99346, 4222.57422]),
    ([112.93549, 199.2446, 422.29234]),
    ([1994.49654, 940.23452, 425.24566]),
    ([1994.496541234566, 940.2345298765, 425.2456612334]),  # Those prices that will be cut when put in DB
]


@pytest.mark.parametrize("prices", PRICE_SPEC)
@pytest.mark.django_db
def test_rounding(prices):
    expected = 0
    for p in prices:
        expected += bankers_round(p, 2)

    order = create_empty_order(prices_include_tax=False)
    order.save()
    for x, price in enumerate(prices):
        ol = OrderLine(
            order=order,
            type=OrderLineType.OTHER,
            quantity=1,
            text="Thing",
            ordering=x,
            base_unit_price=order.shop.create_price(price),
        )
        ol.save()
    order.cache_prices()
    for x, order_line in enumerate(order.lines.all().order_by("ordering")):
        price = Decimal(prices[x]).quantize(Decimal(".1") ** 9)

        # make sure prices are in database with original precision
        assert order_line.base_unit_price == order.shop.create_price(price)

        # make sure the line taxless price is rounded
        assert order_line.taxless_price == order.shop.create_price(bankers_round(price, 2))

        # Check that total prices calculated from priceful parts still matches
        assert _get_taxless_price(order_line) == order_line.taxless_price
        assert _get_taxful_price(order_line) == order_line.taxful_price

        # make sure the line price is rounded
        assert order_line.price == order.shop.create_price(price)

    # make sure order total is rounded
    assert order.taxless_total_price == order.shop.create_price(bankers_round(expected, 2))


@pytest.mark.parametrize("prices", PRICE_SPEC)
@pytest.mark.django_db
def test_order_source_rounding(prices):
    shop = Shop.objects.create(
        name="test", identifier="test", status=ShopStatus.ENABLED, public_name="test", prices_include_tax=False
    )
    expected = 0
    for p in prices:
        expected += bankers_round(p, 2)

    source = BasketishOrderSource(shop)
    for x, price in enumerate(prices):
        source.add_line(
            type=OrderLineType.OTHER,
            quantity=1,
            text=x,
            base_unit_price=source.create_price(price),
            ordering=x,
        )

    for x, order_source in enumerate(source.get_lines()):
        price = Decimal(prices[x]).quantize(Decimal(".1") ** 9)

        # make sure prices are in database with original precision
        assert order_source.base_unit_price == source.shop.create_price(price)

        # make sure the line taxless price is rounded
        assert order_source.taxless_price == source.shop.create_price(bankers_round(price, 2))

        # Check that total prices calculated from priceful parts still matches
        assert _get_taxless_price(order_source) == order_source.taxless_price
        assert _get_taxful_price(order_source) == order_source.taxful_price

        # make sure the line price is rounded
        assert order_source.price == source.shop.create_price(price)

    # make sure order total is rounded
    assert source.taxless_total_price == source.shop.create_price(bankers_round(expected, 2))


@pytest.mark.parametrize("prices", PRICE_SPEC)
@pytest.mark.django_db
def test_rounding_with_taxes(prices):
    shop = get_default_shop()
    supplier = get_default_supplier()

    order = create_empty_order(shop=shop)
    order.save()
    product = create_product("test_sku", shop=shop, supplier=supplier)
    tax_rate = Decimal("0.22222")
    for x, price in enumerate(prices):
        add_product_to_order(
            order,
            supplier,
            product,
            quantity=Decimal("2.22"),
            taxless_base_unit_price=Decimal(price),
            tax_rate=tax_rate,
        )
    order.cache_prices()
    for x, order_line in enumerate(order.lines.all().order_by("ordering")):
        # Check that total prices calculated from priceful parts still matches
        assert _get_taxless_price(order_line) == order_line.taxless_price
        assert _get_taxful_price(order_line) == order_line.taxful_price
        assert order_line.price == (order_line.base_unit_price * order_line.quantity - order_line.discount_amount)


def _get_taxless_price(line):
    return bankers_round(line.taxless_base_unit_price * line.quantity - line.taxless_discount_amount, 2)


def _get_taxful_price(line):
    return bankers_round(line.taxful_base_unit_price * line.quantity - line.taxful_discount_amount, 2)
