# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from decimal import Decimal

from shuup.core.pricing import Priceful, TaxfulPrice, TaxlessPrice
from shuup.utils import babel_precision_provider
from shuup.utils.money import Money, set_precision_provider


class Line(Priceful):
    base_unit_price = None
    quantity = None
    discount_amount = None
    tax_amount = None

    def __init__(self, base_unit_price, quantity, discount_amount, tax_amount):
        self.base_unit_price = base_unit_price
        self.quantity = quantity
        self.discount_amount = discount_amount
        self.tax_amount = tax_amount


line = Line(
    base_unit_price=TaxfulPrice(5, "EUR"),
    quantity=9,
    discount_amount=TaxfulPrice(12, "EUR"),
    tax_amount=Money(3, "EUR"),
)
line2 = Line(
    base_unit_price=TaxfulPrice(10, "EUR"),
    quantity=123,
    discount_amount=TaxfulPrice(0, "EUR"),
    tax_amount=Money(123, "EUR"),
)


def setup_module(module):
    # uses the get_precision to avoiding db hits
    set_precision_provider(babel_precision_provider.get_precision)


def test_price():
    assert line.price == TaxfulPrice(33, "EUR")  # 5 * 9 - 12


def test_discounted_unit_price():
    assert line.discounted_unit_price == TaxfulPrice(33, "EUR") / 9


def test_discount_rate():
    assert line.discount_rate == Decimal(12) / 45


def test_discount_percentage():
    assert line.discount_percentage == 100 * (Decimal(12) / 45)


def test_is_discounted():
    assert line.is_discounted == True
    assert line2.is_discounted == False


def test_unit_discount_amount():
    assert line.unit_discount_amount == TaxfulPrice(12, "EUR") / 9


def test_taxed_prices():
    assert line.taxful_price == line.price
    assert line.taxless_price == TaxlessPrice(30, "EUR")  # 33 - 3


def test_tax_rate_and_percentage():
    assert_almost_equal(line.tax_rate, Decimal("0.1"))  # 3 / 30
    assert_almost_equal(line.tax_percentage, 10)


def test_taxed_base_unit_prices():
    assert_almost_equal(line.taxless_base_unit_price, TaxlessPrice(5, "EUR") / Decimal("1.1"))
    assert line.taxful_base_unit_price == TaxfulPrice(5, "EUR")


def test_taxed_discounted_unit_prices():
    assert_almost_equal(line.taxless_discounted_unit_price, TaxlessPrice(33, "EUR") / Decimal("1.1") / 9)
    assert line.taxful_discounted_unit_price == TaxfulPrice(33, "EUR") / 9


def test_taxed_discount_amounts():
    assert_almost_equal(line.taxless_discount_amount, TaxlessPrice(12, "EUR") / Decimal("1.1"))

    assert line.taxful_discount_amount == TaxfulPrice(12, "EUR")


def test_tax_special_cases1():
    all_tax_line1 = Line(
        base_unit_price=TaxfulPrice(25, "EUR"),
        quantity=5,
        discount_amount=TaxfulPrice(25, "EUR"),
        tax_amount=Money(100, "EUR"),
    )
    assert all_tax_line1.taxful_price == TaxfulPrice(100, "EUR")
    assert all_tax_line1.taxless_price == TaxlessPrice(0, "EUR")
    assert all_tax_line1.taxful_discount_amount == TaxfulPrice(25, "EUR")
    assert all_tax_line1.taxless_discount_amount == TaxlessPrice(0, "EUR")
    assert all_tax_line1.tax_rate == 0
    assert all_tax_line1.taxful_base_unit_price == TaxfulPrice(25, "EUR")
    assert all_tax_line1.taxless_base_unit_price == TaxlessPrice(0, "EUR")


def test_tax_special_cases2():
    all_tax_line2 = Line(
        base_unit_price=TaxlessPrice(0, "EUR"),
        quantity=5,
        discount_amount=TaxlessPrice(0, "EUR"),
        tax_amount=Money(100, "EUR"),
    )
    assert all_tax_line2.taxful_price == TaxfulPrice(100, "EUR")
    assert all_tax_line2.taxless_price == TaxlessPrice(0, "EUR")
    assert all_tax_line2.taxful_discount_amount == TaxfulPrice(0, "EUR")
    assert all_tax_line2.taxless_discount_amount == TaxlessPrice(0, "EUR")
    assert all_tax_line2.tax_rate == 0
    # assert all_tax_line2.taxful_base_unit_price == TaxfulPrice(20, 'EUR')
    assert all_tax_line2.taxless_base_unit_price == TaxlessPrice(0, "EUR")


def test_tax_special_cases3():
    taxless_line = Line(
        base_unit_price=TaxfulPrice(0, "EUR"),
        quantity=0,
        discount_amount=TaxfulPrice(0, "EUR"),
        tax_amount=Money(0, "EUR"),
    )
    assert taxless_line.taxful_price == TaxfulPrice(0, "EUR")
    assert taxless_line.taxless_price == TaxlessPrice(0, "EUR")

    assert taxless_line.base_unit_price == TaxfulPrice(0, "EUR")
    assert taxless_line.taxful_base_unit_price == TaxfulPrice(0, "EUR")
    assert taxless_line.taxless_base_unit_price == TaxlessPrice(0, "EUR")

    assert taxless_line.discount_amount == TaxfulPrice(0, "EUR")
    assert taxless_line.taxful_discount_amount == TaxfulPrice(0, "EUR")
    assert taxless_line.taxless_discount_amount == TaxlessPrice(0, "EUR")

    assert taxless_line.price == TaxfulPrice(0, "EUR")
    assert taxless_line.taxful_price == TaxfulPrice(0, "EUR")
    assert taxless_line.taxless_price == TaxlessPrice(0, "EUR")

    assert taxless_line.base_price == TaxfulPrice(0, "EUR")
    assert taxless_line.taxful_base_price == TaxfulPrice(0, "EUR")
    assert taxless_line.taxless_base_price == TaxlessPrice(0, "EUR")

    assert taxless_line.unit_discount_amount == TaxfulPrice(0, "EUR")
    assert taxless_line.taxful_unit_discount_amount == TaxfulPrice(0, "EUR")
    assert taxless_line.taxless_unit_discount_amount == TaxlessPrice(0, "EUR")

    assert taxless_line.discount_rate == 0
    assert taxless_line.tax_rate == 0


def assert_almost_equal(x, y):
    assert Decimal(abs(x - y)) < 0.0000000000000000000000001


def test_property_docs():
    assert Line.taxful_discount_amount.__doc__ == "Taxful `discount_amount`"
    assert Line.taxless_discount_amount.__doc__ == "Taxless `discount_amount`"
