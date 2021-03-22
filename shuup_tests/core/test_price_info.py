# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from decimal import Decimal

from shuup.core.pricing import PriceInfo, TaxlessPrice


def price(value):
    return TaxlessPrice(value, "EUR")


def test_no_discount():
    pi = PriceInfo(price(100), price(100), 1)
    assert not pi.is_discounted
    assert pi.discount_percentage == 0
    assert pi.discount_amount == price(0)


def test_with_discounts():
    pi = PriceInfo(price(75), price(100), 1)
    assert pi.is_discounted
    assert pi.discount_percentage == 25
    assert pi.discount_amount == price(25)


def test_quantity_not_one_without_discounts():
    pi = PriceInfo(price(123), price(123), 10)
    assert pi.price == price(123)
    assert pi.base_price == price(123)
    assert pi.discount_amount == price(0)
    assert pi.discount_percentage == 0
    assert pi.discounted_unit_price == price("12.3")
    assert pi.base_unit_price == price("12.3")
    assert pi.unit_discount_amount == price(0)


def test_quantity_not_one_with_discounts():
    pi = PriceInfo(price("27.5"), price(100), Decimal(2.5))
    assert pi.price == price("27.5")
    assert pi.base_price == price(100)
    assert pi.discount_amount == price("72.5")
    assert pi.discount_percentage == Decimal("72.5")
    assert pi.discounted_unit_price == price(11)
    assert pi.base_unit_price == price(40)
    assert pi.unit_discount_amount == price(29)


def test_discount_percentage_special_cases():
    pi1 = PriceInfo(price(10), price(0), quantity=1)
    assert pi1.discount_percentage == 0


def test_repr():
    pi1 = PriceInfo(price("0.3"), price(42), Decimal("1.3"))
    r1 = "PriceInfo(" "TaxlessPrice('0.3', 'EUR'), TaxlessPrice('42', 'EUR'), Decimal('1.3')" ")"
    assert repr(pi1) == r1

    pi2 = PriceInfo(price("1.3"), price(42), Decimal("1.3"), expires_on=1483272000)
    r2 = "PriceInfo(" "TaxlessPrice('1.3', 'EUR'), TaxlessPrice('42', 'EUR')," " Decimal('1.3'), expires_on=1483272000)"
    assert repr(pi2) == r2
