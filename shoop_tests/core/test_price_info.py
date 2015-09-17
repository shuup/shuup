# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from decimal import Decimal

from shoop.core.pricing import TaxlessPrice
from shoop.core.pricing.price_info import PriceInfo


def test_no_discount():
    pi = PriceInfo(TaxlessPrice(100), TaxlessPrice(100), 1)
    assert not pi.is_discounted
    assert pi.discount_percentage == 0
    assert pi.discount_amount == TaxlessPrice(0)


def test_with_discounts():
    pi = PriceInfo(TaxlessPrice(75), TaxlessPrice(100), 1)
    assert pi.is_discounted
    assert pi.discount_percentage == 25
    assert pi.discount_amount == TaxlessPrice(25)


def test_quantity_not_one_without_discounts():
    pi = PriceInfo(TaxlessPrice(123), TaxlessPrice(123), 10)
    assert pi.price == TaxlessPrice(123)
    assert pi.base_price == TaxlessPrice(123)
    assert pi.discount_amount == TaxlessPrice(0)
    assert pi.discount_percentage == 0
    assert pi.unit_price == TaxlessPrice('12.3')
    assert pi.unit_base_price == TaxlessPrice('12.3')
    assert pi.unit_discount_amount == TaxlessPrice(0)


def test_quantity_not_one_with_discounts():
    pi = PriceInfo(TaxlessPrice('27.5'), TaxlessPrice(100), Decimal(2.5))
    assert pi.price == TaxlessPrice('27.5')
    assert pi.base_price == TaxlessPrice(100)
    assert pi.discount_amount == TaxlessPrice('72.5')
    assert pi.discount_percentage == Decimal('72.5')
    assert pi.unit_price == TaxlessPrice(11)
    assert pi.unit_base_price == TaxlessPrice(40)
    assert pi.unit_discount_amount == TaxlessPrice(29)


def test_discount_percentage_special_cases():
    pi1 = PriceInfo(TaxlessPrice(10), TaxlessPrice(0), quantity=1)
    assert pi1.discount_percentage == 0


def test_repr():
    pi1 = PriceInfo(TaxlessPrice('0.3'), TaxlessPrice(42), Decimal('1.3'))
    r1 = "PriceInfo(TaxlessPrice('0.3'), TaxlessPrice('42'), Decimal('1.3'))"
    assert repr(pi1) == r1

    pi2 = PriceInfo(
        TaxlessPrice('1.3'), TaxlessPrice(42),
        Decimal('1.3'), expires_on=1483272000)
    r2 = (
        "PriceInfo("
        "TaxlessPrice('1.3'), TaxlessPrice('42'),"
        " Decimal('1.3'), expires_on=1483272000)")
    assert repr(pi2) == r2
