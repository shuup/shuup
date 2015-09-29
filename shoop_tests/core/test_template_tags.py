# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from decimal import Decimal
from django.utils import translation
from shoop.core.templatetags.shoop_common import percent, number, money
from shoop.utils.money import Money


def nbsp(x):
    """
    Convert space to non-breaking space.
    """
    return x.replace(" ", "\xa0")

def usd(value):
    """
    Get Money with USD currency for given value.
    """
    return Money(value, "USD")


def test_number_formatters_en():
    with translation.override("en-US"):
        assert percent(Decimal("0.38")) == "38%"
        assert number(Decimal("38.00000")) == "38"
        assert number(Decimal("38.05000")) == "38.05"


def test_number_formatters_fi():
    with translation.override("fi-FI"):
        assert percent(Decimal("0.38")) == nbsp("38 %")
        assert number(Decimal("38.00000")) == "38"
        assert number(Decimal("38.05000")) == "38,05"


def test_money_formatter_en():
    with translation.override("en-US"):
        assert money(Money("29.99", "USD")) == "$29.99"
        assert money(Money("29.99", "EUR")) == "€29.99"
        assert money(Money("29.99", "GBP")) == "£29.99"
        assert money(Money("29.99", "CAD")) == "CA$29.99"
        assert money(Money("29.99", "JPY")) == "¥29.99"
        assert money(Money("29.99", "CNY")) == "CN¥29.99"
        assert money(Money("29.99", "KRW")) == "₩29.99"
        assert money(Money("29.99", "SEK")) == "SEK29.99"


def test_money_formatter_fi():
    with translation.override("fi-FI"):
        assert money(Money("29.99", "USD")) == nbsp("29,99 $")
        assert money(Money("29.99", "EUR")) == nbsp("29,99 €")
        assert money(Money("29.99", "GBP")) == nbsp("29,99 £")
        assert money(Money("29.99", "CAD")) == nbsp("29,99 CAD")
        assert money(Money("29.99", "JPY")) == nbsp("29,99 ¥")
        assert money(Money("29.99", "CNY")) == nbsp("29,99 CNY")
        assert money(Money("29.99", "KRW")) == nbsp("29,99 KRW")
        assert money(Money("29.99", "SEK")) == nbsp("29,99 SEK")


def test_money_formatter_default_digit_expanding():
    with translation.override("en-US"):
        assert money(usd(0)) == "$0.00"
        assert money(usd(1)) == "$1.00"


def test_money_formatter_default_digit_rounding():
    with translation.override("en-US"):
        assert money(usd("1.234")) == "$1.23"
        assert money(usd("1.235")) == "$1.24"
        assert money(usd("1.244")) == "$1.24"
        assert money(usd("1.245")) == "$1.24"
        assert money(usd("1.254")) == "$1.25"
        assert money(usd("1.255")) == "$1.26"
        assert money(usd("1.111111111111")) == "$1.11"


def test_money_formatter_digit_grouping():
    with translation.override("en-US"):
        assert money(usd(12345678)) == "$12,345,678.00"
    with translation.override("fi-FI"):
        assert money(usd(12345678)) == nbsp("12 345 678,00 $")
    with translation.override("ar-QA"):
        assert money(usd(12345678)) == nbsp("US$12345678.00")


def test_money_formatter_with_specified_digits():
    with translation.override("en-US"):
        assert money(usd("1234.123456"), digits=0) == "$1,234"
        assert money(usd("1234.123456"), digits=1) == "$1,234.1"
        assert money(usd("1234.123456"), digits=3) == "$1,234.123"
        assert money(usd("1234.123456"), digits=4) == "$1,234.1235"
        assert money(usd("1234.123456"), digits=5) == "$1,234.12346"
        assert money(usd("1234.123456"), digits=6) == "$1,234.123456"
    with translation.override("fi-FI"):
        assert money(usd("1234.123456"), digits=0) == nbsp("1 234 $")
        assert money(usd("1234.123456"), digits=1) == nbsp("1 234,1 $")
        assert money(usd("1234.123456"), digits=3) == nbsp("1 234,123 $")
        assert money(usd("1234.123456"), digits=4) == nbsp("1 234,1235 $")
        assert money(usd("1234.123456"), digits=5) == nbsp("1 234,12346 $")
        assert money(usd("1234.123456"), digits=6) == nbsp("1 234,123456 $")


def test_money_formatter_with_extra_digits():
    with translation.override("en-US"):
        assert money(usd("1234.123456"), widen=0) == "$1,234.12"
        assert money(usd("1234.123456"), widen=1) == "$1,234.123"
        assert money(usd("1234.123456"), widen=2) == "$1,234.1235"
        assert money(usd("1234.123456"), widen=3) == "$1,234.12346"
        assert money(usd("1234.123456"), widen=4) == "$1,234.123456"
    with translation.override("fi-FI"):
        assert money(usd("1234.123456"), widen=0) == nbsp("1 234,12 $")
        assert money(usd("1234.123456"), widen=1) == nbsp("1 234,123 $")
        assert money(usd("1234.123456"), widen=2) == nbsp("1 234,1235 $")
        assert money(usd("1234.123456"), widen=3) == nbsp("1 234,12346 $")
        assert money(usd("1234.123456"), widen=4) == nbsp("1 234,123456 $")
