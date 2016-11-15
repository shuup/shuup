# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
import math
from django.conf import settings
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_DOWN
from mock import patch

import shuup.utils.money as money_module
from shuup.core.pricing import TaxfulPrice, TaxlessPrice
from shuup.utils.money import (
    make_precision, get_babel_digits, get_precision, Money, set_precision_provider_function
)

PRICES_SPEC = [
    ([1,2,3,4]),
    ([1.23223, 12.24442, 42.26233]),
    ([1223.46636, 13.24655, 411.234554]),
    ([101.74363, 12.99346, 4222.57422]),
    ([112.93549, 199.2446, 422.29234]),
    ([1994.49654, 940.23452, 425.24566]),
    ([1994.496541234566, 940.2345298765, 425.2456612334]),
]


def test_money_init_does_not_call_settings():
    def guarded_getattr(self, name):
        assert False, 'nobody should read settings yet'

    with patch.object(type(settings), '__getattr__', guarded_getattr):
        Money(42, 'EUR')


def test_money_without_currency():
    with pytest.raises(TypeError):
        Money(42)


def test_money_init_from_money():
    assert Money(Money(123, 'GBP')) == Money(123, 'GBP')


def test_money_init_from_value_with_currency():
    class Dollar(int):
        currency = 'USD'

    assert Money(Dollar(42)) == Money(42, 'USD')


def test_units_match():
    class XxxMoney(int):
        currency = 'XXX'

    m1 = Money(1, 'EUR')
    m2 = Money(2, 'EUR')
    m3 = Money(3, 'XXX')
    m4 = XxxMoney(4)

    assert m1.unit_matches_with(m2)
    assert not m1.unit_matches_with(m3)
    assert m3.unit_matches_with(m4)


def test_repr():
    assert repr(Money(42, 'EUR')) == "Money('42', 'EUR')"
    assert repr(Money('42.123', 'EUR')) == "Money('42.123', 'EUR')"
    assert repr(Money('42.0', 'EUR')) == "Money('42.0', 'EUR')"
    assert repr(Money('42.123', 'EUR')) == "Money('42.123', 'EUR')"
    assert repr(Money('42.123', 'USD')) == "Money('42.123', 'USD')"


def test_str():
    assert str(Money('42.25', 'EUR')) == '42.25 EUR'
    assert str(Money('100', 'USD')) == '100 USD'

    assert str(Money(42, 'EUR')) == '42 EUR'
    assert str(Money('12.345', 'EUR')) == '12.345 EUR'


def test_money_basics():
    m1 = Money(1, 'EUR')
    m2 = Money(2, 'EUR')
    m3 = Money(3, 'EUR')
    assert m1 + m2 == m3
    assert m3 - m1 == m2
    assert m3.value == 3
    assert m3 / m2 == m3.value / m2.value


def test_as_rounds_returns_same_type():
    set_precision_provider_function(get_precision)

    value = Decimal(0.44430489234026)
    tfp = TaxfulPrice(value, 'USD')
    assert type(tfp) == type(tfp.as_rounded())

    tlp = TaxlessPrice(value, 'USD')
    assert type(tlp) == type(tlp.as_rounded())


def test_money_currency_provider_function():
    with pytest.raises(AssertionError):
        set_precision_provider_function(3)

    set_precision_provider_function(get_precision)


def test_make_precision():
    assert make_precision(0) == Decimal('1')
    assert make_precision(1) == Decimal('0.1')
    assert make_precision(2) == Decimal('0.01')
    assert make_precision(3) == Decimal('0.001')
    assert make_precision(4) == Decimal('0.0001')
    assert make_precision(5) == Decimal('0.00001')


@pytest.mark.parametrize("prices", PRICES_SPEC)
def test_money_as_rounded_values(prices):
    set_precision_provider_function(get_precision)

    # clear the caches
    money_module.CURRENCY_PRECISIONS.clear()
    money_module.DIGITS_PRECISIONS.clear()

    fallback_precision = make_precision(2)

    currencies = ["USD", "JPY", "MXN", "BRL"]
    currency_digits = list(map(get_babel_digits, currencies))

    # round values
    for currency, digits in zip(currencies, currency_digits):
        for price in prices:
            precision = make_precision(digits)
            right_price = Decimal(price).quantize(precision)
            fallback_price = Decimal(price).quantize(fallback_precision)

            # test using the currency
            assert Money(price, currency).as_rounded().value == right_price
            assert TaxfulPrice(price, currency).as_rounded().value == right_price
            assert TaxlessPrice(price, currency).as_rounded().value == right_price

            # test using digits
            assert Money(price, currency).as_rounded(digits).value == right_price
            assert TaxfulPrice(price, currency).as_rounded(digits).value == right_price
            assert TaxlessPrice(price, currency).as_rounded(digits).value == right_price

            # test using not existent currency code - use fallback
            assert Money(price, "XTS").as_rounded().value == fallback_price
            assert TaxfulPrice(price, "XTS").as_rounded().value == fallback_price
            assert TaxlessPrice(price, "XTS").as_rounded().value == fallback_price


def test_money_as_rounded():
    set_precision_provider_function(get_precision)

    v1 = Decimal('2.345')
    v2 = Decimal('2.344')

    assert Money(v1, 'EUR').as_rounded(digits=2).value == Decimal(v1).quantize(make_precision(2))
    assert Money(v2, 'EUR').as_rounded(digits=2).value == Decimal(v2).quantize(make_precision(2))

    r1 = Money(v1, 'EUR').as_rounded(digits=2, rounding=ROUND_HALF_DOWN).value
    r2 = v1.quantize(make_precision(2), rounding=ROUND_HALF_DOWN)
    assert r1 == r2

    r1 = Money(v1, 'EUR').as_rounded(digits=3, rounding=ROUND_FLOOR).value
    r2 = v1.quantize(make_precision(3), rounding=ROUND_FLOOR)
    assert r1 == r2


def test_set_precision_provider():
    # check if the set method works
    set_precision_provider_function(get_precision)
    assert money_module._precision_provider_func == get_precision
    set_precision_provider_function(int)
    assert money_module._precision_provider_func == int
    set_precision_provider_function(get_precision)
