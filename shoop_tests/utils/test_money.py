# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.conf import settings
from mock import patch

from shoop.utils.money import Money


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
