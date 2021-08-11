# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from decimal import Decimal
from django.conf import settings
from django.test import override_settings
from django.utils import translation
from jinja2 import Template
from mock import patch

from shuup.core.models import Shop
from shuup.core.templatetags.shuup_common import (
    get_global_configuration,
    get_shop_configuration,
    get_shuup_version,
    money,
    number,
    percent,
    safe_product_description,
    safe_vendor_description,
    shuup_static,
)
from shuup.core.utils.static import get_shuup_static_url
from shuup.utils.money import Money


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


def en_percent(num, ndigits="not-given"):
    """
    Format given number as percent in en-US locale.
    """
    with translation.override("en-US"):
        if ndigits == "not-given":
            return percent(Decimal(num))
        else:
            return percent(Decimal(num), ndigits)


def test_percent_formatter_simple():
    assert en_percent("0.1") == "10%"
    assert en_percent("0.16") == "16%"
    assert en_percent("0.99") == "99%"


def test_percent_formatter_special_numbers():
    assert en_percent("0") == "0%"
    assert en_percent("1") == "100%"
    assert en_percent("2") == "200%"
    assert en_percent("3000") == "300,000%"
    assert en_percent("-0.1") == "-10%"
    assert en_percent("-1") == "-100%"
    assert en_percent("-10") == "-1,000%"


def test_percent_formatter_default_is_0_digits():
    assert en_percent("0.111") == "11%"
    assert en_percent("0.111111") == "11%"


def test_percent_formatter_more_digits():
    assert en_percent("0.166", 1) == "16.6%"
    assert en_percent("0.166", 2) == "16.60%"
    assert en_percent("0.166", 3) == "16.600%"
    assert en_percent("0.166", 9) == "16.600000000%"
    assert en_percent("0.1", 1) == "10.0%"
    assert en_percent("0.1", 2) == "10.00%"
    assert en_percent("0.1", 3) == "10.000%"
    assert en_percent("0", 1) == "0.0%"


def test_percent_formatter_fewer_digits():
    assert en_percent("0.11111", 2) == "11.11%"
    assert en_percent("0.11111", 1) == "11.1%"
    assert en_percent("0.11111", 0) == "11%"


def test_percent_formatter_fewer_digits_rounding():
    assert en_percent("0.2714", 1) == "27.1%"
    assert en_percent("0.2715", 1) == "27.2%"  # towards even
    assert en_percent("0.2716", 1) == "27.2%"
    assert en_percent("0.2724", 1) == "27.2%"
    assert en_percent("0.2725", 1) == "27.2%"  # towards even
    assert en_percent("0.2726", 1) == "27.3%"


def test_money_formatter_en():
    with translation.override("en-US"):
        assert money(Money("29.99", "USD")) == "$29.99"
        assert money(Money("29.99", "EUR")) == "€29.99"
        assert money(Money("29.99", "GBP")) == "£29.99"
        assert money(Money("29.99", "CAD")) == "CA$29.99"
        assert money(Money("29.99", "JPY")) == "¥30"  # No such thing as a decimal yen!
        assert money(Money("29.99", "CNY")) == "CN¥29.99"
        assert money(Money("29.99", "KRW")) == "₩30"  # the 1/100 subunit "jeon" is theoretical and not in use
        assert money(Money("29.99", "SEK")) == "kr29.99"


def test_money_formatter_fi():
    with translation.override("fi-FI"):
        assert money(Money("29.99", "USD")) == nbsp("29,99 $")
        assert money(Money("29.99", "EUR")) == nbsp("29,99 €")
        assert money(Money("29.99", "GBP")) == nbsp("29,99 £")
        assert money(Money("29.99", "CAD")) == nbsp("29,99 CAD")
        assert money(Money("29.99", "JPY")) == nbsp("30 ¥")  # No such thing as a decimal yen!
        assert money(Money("29.99", "CNY")) == nbsp("29,99 CNY")
        assert money(Money("29.99", "KRW")) == nbsp("30 KRW")  # the 1/100 subunit "jeon" is theoretical and not in use
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
        assert money(usd(12345678)) == nbsp("US$ 12,345,678.00")


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


@patch("shuup.configuration.get")
def test_get_shop_configuration(conf_get_mock, rf):
    shop = Shop(identifier="da-shop", name="The Shop")
    request = rf.get("/")
    request.shop = shop
    ctx = Template("").new_context({"request": request})

    get_shop_configuration(ctx, "some_variable")
    conf_get_mock.assert_called_once_with(shop, "some_variable", None)

    conf_get_mock.reset_mock()

    get_shop_configuration(ctx, "some_variable", "default")
    conf_get_mock.assert_called_once_with(shop, "some_variable", "default")


@patch("shuup.configuration.get")
def test_get_global_configuration(conf_get_mock, rf):
    get_global_configuration("some_variable")
    conf_get_mock.assert_called_once_with(None, "some_variable", None)


@patch("shuup.configuration.get")
def test_get_global_configuration_with_default(conf_get_mock, rf):
    get_global_configuration("some_variable", "default")
    conf_get_mock.assert_called_once_with(None, "some_variable", "default")


def test_safe_product_description():
    text = "<strong>product description</strong>\nSome text here."

    with override_settings(SHUUP_ADMIN_ALLOW_HTML_IN_PRODUCT_DESCRIPTION=True):
        assert safe_product_description(text) == text

    with override_settings(SHUUP_ADMIN_ALLOW_HTML_IN_PRODUCT_DESCRIPTION=False):
        assert safe_product_description(text) == "<p>product description<br>Some text here.</p>"


def test_safe_vendor_description():
    text = "<strong>vendor description</strong>\nSome text here."

    with override_settings(SHUUP_ADMIN_ALLOW_HTML_IN_VENDOR_DESCRIPTION=True):
        assert safe_vendor_description(text) == text

    with override_settings(SHUUP_ADMIN_ALLOW_HTML_IN_VENDOR_DESCRIPTION=False):
        assert (
            safe_vendor_description(text) == "<p>&lt;strong&gt;vendor description&lt;/strong&gt;<br>Some text here.</p>"
        )


def test_get_shuup_static_url():
    assert "test.js?v=%s" % get_shuup_version() in get_shuup_static_url("test.js")
    assert get_shuup_static_url("test.js") == shuup_static("test.js")
    assert "test.css?v=" in get_shuup_static_url("test.css", "django")
    assert get_shuup_static_url("test2.js", "django") == shuup_static("test2.js", "django")
    assert shuup_static("test3.js") != shuup_static("test3.js", "django")
