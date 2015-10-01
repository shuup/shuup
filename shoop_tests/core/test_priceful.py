# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from decimal import Decimal as D

from shoop.core.pricing import TaxfulPrice, TaxlessPrice
from shoop.core.pricing.priceful import Priceful
from shoop.utils.money import Money


class Line(Priceful):
    def __init__(self, base_unit_price, quantity, discount_amount, tax_amount):
        self.base_unit_price = base_unit_price
        self.quantity = quantity
        self.discount_amount = discount_amount
        self.tax_amount = tax_amount

def get_line():
    return Line(
        base_unit_price=TaxfulPrice(5, 'EUR'),
        quantity=9,
        discount_amount=TaxfulPrice(12, 'EUR'),
        tax_amount=Money(3, 'EUR')
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


def test_base_unit_price():
    line = get_line()

    assert_almost_equal(
        line.taxless_base_unit_price, TaxlessPrice(5, 'EUR') / D('1.1'))
    assert line.taxful_base_unit_price == TaxfulPrice(5, 'EUR')


def test_discount_amount():
    line = get_line()
    assert_almost_equal(
        line.taxless_discount_amount, TaxlessPrice(12, 'EUR') / D('1.1'))

    assert line.taxful_discount_amount == TaxfulPrice(12, 'EUR')


def assert_almost_equal(x, y):
    assert D(abs(x - y)) < 0.0000000000000000000000001
