# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from decimal import Decimal

from shuup.core.models import OrderLine
from shuup.core.models import OrderLineType
from shuup.core.models import Shop
from shuup.core.models import ShopStatus
from shuup.testing.factories import create_empty_order
from shuup.utils.numbers import bankers_round
from shuup_tests.utils.basketish_order_source import BasketishOrderSource

PRICE_SPEC = [
    ([1,2,3,4]),
    ([1,2,3,6]),
    ([1,2,3,8]),
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
    currency = order.shop.currency
    for x, price in enumerate(prices):
        ol = OrderLine(
            order=order,
            type=OrderLineType.OTHER,
            quantity=1,
            text="Thing",
            ordering=x,
            base_unit_price=order.shop.create_price(price)
        )
        ol.save()
    order.cache_prices()
    for x, order_line in enumerate(order.lines.all().order_by("ordering")):
        price = Decimal(prices[x]).quantize(Decimal(".1") ** 9)

        # make sure prices are in database with original precision
        assert order_line.base_unit_price == order.shop.create_price(price)

        # make sure the line taxless price is rounded
        assert order_line.taxless_price == order.shop.create_price(bankers_round(price, 2))

        # make sure the line price is rounded
        assert order_line.price == order.shop.create_price(price)

    # make sure order total is rounded
    assert order.taxless_total_price == order.shop.create_price(bankers_round(expected, 2))


@pytest.mark.parametrize("prices", PRICE_SPEC)
@pytest.mark.django_db
def test_order_source_rounding(prices):
    shop = Shop.objects.create(
        name="test",
        identifier="test",
        status=ShopStatus.ENABLED,
        public_name="test",
        prices_include_tax=False
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

        # make sure the line price is rounded
        assert order_source.price == source.shop.create_price(price)

    # make sure order total is rounded
    assert source.taxless_total_price == source.shop.create_price(bankers_round(expected, 2))
