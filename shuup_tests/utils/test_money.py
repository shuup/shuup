# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import math
import pytest
from decimal import ROUND_FLOOR, ROUND_HALF_DOWN, Decimal
from django.conf import settings
from mock import patch

from shuup.utils import babel_precision_provider, money
from shuup.utils.money import Money, set_precision_provider


def test_money_init_does_not_call_settings():
    def guarded_getattr(self, name):
        assert False, "nobody should read settings yet"

    with patch.object(type(settings), "__getattr__", guarded_getattr):
        Money(42, "EUR")


def test_money_without_currency():
    with pytest.raises(TypeError):
        Money(42)


def test_money_init_from_money():
    assert Money(Money(123, "GBP")) == Money(123, "GBP")


def test_money_init_from_value_with_currency():
    class Dollar(int):
        currency = "USD"

    assert Money(Dollar(42)) == Money(42, "USD")


def test_units_match():
    class XxxMoney(int):
        currency = "XXX"

    m1 = Money(1, "EUR")
    m2 = Money(2, "EUR")
    m3 = Money(3, "XXX")
    m4 = XxxMoney(4)

    assert m1.unit_matches_with(m2)
    assert not m1.unit_matches_with(m3)
    assert m3.unit_matches_with(m4)


def test_repr():
    assert repr(Money(42, "EUR")) == "Money('42', 'EUR')"
    assert repr(Money("42.123", "EUR")) == "Money('42.123', 'EUR')"
    assert repr(Money("42.0", "EUR")) == "Money('42.0', 'EUR')"
    assert repr(Money("42.123", "EUR")) == "Money('42.123', 'EUR')"
    assert repr(Money("42.123", "USD")) == "Money('42.123', 'USD')"


def test_str():
    assert str(Money("42.25", "EUR")) == "42.25 EUR"
    assert str(Money("100", "USD")) == "100 USD"

    assert str(Money(42, "EUR")) == "42 EUR"
    assert str(Money("12.345", "EUR")) == "12.345 EUR"


def test_money_basics():
    m1 = Money(1, "EUR")
    m2 = Money(2, "EUR")
    m3 = Money(3, "EUR")
    assert m1 + m2 == m3
    assert m3 - m1 == m2
    assert m3.value == 3
    assert m3 / m2 == m3.value / m2.value


def test_as_rounded_returns_same_type():
    set_precision_provider(babel_precision_provider.get_precision)

    class CoolMoney(Money):
        is_cool = True

    amount = CoolMoney("0.4939389", "USD")
    assert type(amount.as_rounded()) == CoolMoney
    assert amount.as_rounded().is_cool


@pytest.mark.parametrize("currency,digits", [("USD", 2), ("EUR", 2), ("JPY", 0), ("CLF", 4), ("BRL", 2)])
def test_as_rounded_values(currency, digits):
    set_precision_provider(babel_precision_provider.get_precision)

    amounts = [
        "1",
        "2",
        "3",
        "4",
        "1.23223",
        "12.24442",
        "42.26233",
        "1223.46636",
        "13.24655",
        "411.234554",
        "101.74363",
        "12.99346",
        "4222.57422",
        "112.93549",
        "199.2446",
        "422.29234",
        "1994.49654",
        "940.23452",
        "425.24566",
        "1994.496541234566",
        "940.2345298765",
        "425.2456612334",
    ]

    for amount in amounts:
        precision = Decimal("0.1") ** digits

        rounded = Decimal(amount).quantize(precision)
        rounded2 = Decimal(amount).quantize(Decimal("0.01"))
        rounded3 = Decimal(amount).quantize(Decimal("0.001"))

        # test using the currency
        assert Money(amount, currency).as_rounded().value == rounded

        # test using digits
        assert Money(amount, currency).as_rounded(3).value == rounded3

        # test using not existent currency code
        assert Money(amount, "XTS").as_rounded().value == rounded2


def test_as_rounded_rounding_mode():
    set_precision_provider(babel_precision_provider.get_precision)

    prec2 = Decimal("0.01")
    m1 = Money("2.345", "EUR")
    m2 = Money("2.344", "EUR")

    assert m1.as_rounded(2).value == Decimal("2.34")
    assert m2.as_rounded(2).value == Decimal("2.34")

    from decimal import ROUND_FLOOR, ROUND_HALF_DOWN, ROUND_HALF_UP

    assert m1.as_rounded(2, rounding=ROUND_HALF_DOWN).value == Decimal("2.34")
    assert m2.as_rounded(2, rounding=ROUND_HALF_DOWN).value == Decimal("2.34")
    assert m1.as_rounded(2, rounding=ROUND_HALF_UP).value == Decimal("2.35")
    assert m2.as_rounded(2, rounding=ROUND_HALF_UP).value == Decimal("2.34")
    assert m1.as_rounded(2, rounding=ROUND_FLOOR).value == Decimal("2.34")
    assert m2.as_rounded(2, rounding=ROUND_FLOOR).value == Decimal("2.34")


def test_set_precision_provider():
    def get_precision(currency):
        return None

    set_precision_provider(get_precision)
    assert money._precision_provider == get_precision

    set_precision_provider(babel_precision_provider.get_precision)
    assert money._precision_provider == babel_precision_provider.get_precision


def test_set_precision_provider_with_non_callable():
    with pytest.raises(AssertionError):
        set_precision_provider(3)
