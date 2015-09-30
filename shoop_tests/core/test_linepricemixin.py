# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from decimal import Decimal as D

from shoop.core.pricing import TaxfulPrice, TaxlessPrice
from shoop.core.utils.prices import LinePriceMixin
from shoop.utils.money import Money


class Line(LinePriceMixin):
    def __init__(self, unit_price, quantity, total_discount, total_tax_amount):
        self.unit_price = unit_price
        self.quantity = quantity
        self.total_discount = total_discount
        self.total_tax_amount = total_tax_amount

def get_line():
    return Line(
        unit_price=TaxfulPrice(5, 'EUR'),
        quantity=9,
        total_discount=TaxfulPrice(12, 'EUR'),
        total_tax_amount=Money(3, 'EUR')
    )


def test_totals():
    line = get_line()
    assert line.total_price == TaxfulPrice(33, 'EUR')  # 5 * 9 - 12
    assert line.taxful_total_price == line.total_price
    assert line.taxless_total_price == TaxlessPrice(30, 'EUR')  # 33 - 3


def test_tax_rate_and_percentage():
    line = get_line()
    assert_almost_equal(line.tax_rate, D('0.1'))  # 3 / 30
    assert_almost_equal(line.tax_percentage, 10)


def test_unit_price():
    line = get_line()

    assert_almost_equal(
        line.taxless_unit_price, TaxlessPrice(5, 'EUR') / D('1.1'))
    assert line.taxful_unit_price == TaxfulPrice(5, 'EUR')


def test_total_discount():
    line = get_line()
    assert_almost_equal(
        line.taxless_total_discount, TaxlessPrice(12, 'EUR') / D('1.1'))

    assert line.taxful_total_discount == TaxfulPrice(12, 'EUR')


def assert_almost_equal(x, y):
    assert D(abs(x - y)) < 0.0000000000000000000000001
