# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import decimal
import pytest
import six
from decimal import Decimal

from shuup.utils.numbers import parse_decimal_string, parse_simple_decimal


@pytest.mark.parametrize(
    "input_value, expected_result",
    [
        ("42", Decimal(42)),
        ("-13", Decimal(-13)),
        ("+5", Decimal(5)),
        (".2", Decimal("0.2")),
        ("2.", Decimal("2")),
        ("inf", None),
        ("", None),
        ("+", None),
        ("-", None),
        ("++", None),
        ("--", None),
        ("1-2", None),
        (("9" * 51), None),  # Too long
        ("." + ("9" * 51), None),  # Too long
        (("9" * 50), Decimal("9" * 50)),  # Barely fits
        ("." + ("0" * 49) + "1", Decimal("0." + ("0" * 49) + "1")),
        ("2.5", Decimal("2.5")),
        ("123.456", Decimal("123.456")),
        (" 3", None),
        ("3 ", None),
        (3, None),
        (3, None),
        (0.5, None),
        (float("inf"), None),
        ("1e2", None),
        ("foo", None),
        ("3ä4", None),
    ],
)
def test_parse_simple_decimal(input_value, expected_result):
    if expected_result is not None:
        result = parse_simple_decimal(input_value)
        assert result == expected_result
        assert isinstance(result, Decimal)
        if six.PY2 and isinstance(input_value, six.text_type):
            bytes_input = input_value.encode("utf-8")
            assert parse_simple_decimal(bytes_input) == expected_result
    else:
        assert parse_simple_decimal(input_value, None) is None
        assert parse_simple_decimal(input_value, 0) == 0
        with pytest.raises(ValueError) as exc_info:
            parse_simple_decimal(input_value)
        assert "{}".format(exc_info.value) == (
            "Error! Value `%r` can't be parsed as a simple decimal." % (input_value,)
        )


@pytest.mark.parametrize(
    "input_val, expected_val",
    [
        (0.0, Decimal("0.0")),
        (1.1, Decimal("1.1")),
        (-1.1, Decimal("-1.1")),
        (1e10, Decimal("10000000000")),
        (1e10, Decimal("1e10")),
        (1e-10, Decimal("0.0000000001")),
        (1e-10, Decimal("1e-10")),
    ],
)
def test_parse_decimal_string_with_float_input(input_val, expected_val):
    result = parse_decimal_string(input_val)
    assert result == expected_val


def test_parse_decimal_string_with_normal_input():
    assert parse_decimal_string("42") == Decimal(42)
    assert parse_decimal_string("0") == Decimal(0)
    assert parse_decimal_string(3.5) == Decimal("3.5")
    assert parse_decimal_string(-5) == Decimal(-5)
    assert parse_decimal_string("-5") == Decimal(-5)


def test_parse_decimal_string_with_dirty_input():
    assert parse_decimal_string("1e12") == Decimal(112)
    assert parse_decimal_string("foo1bar 1x2") == Decimal(112)
    assert parse_decimal_string("4a bc2def 8g.h5") == Decimal("428.5")
    assert parse_decimal_string(float("inf")) == Decimal("inf")
    assert parse_decimal_string(float("-inf")) == Decimal("-inf")
    assert str(parse_decimal_string(float("nan"))) == str(Decimal("nan"))
    assert parse_decimal_string("") == Decimal(0)
    assert parse_decimal_string(" ") == Decimal(0)


@pytest.mark.parametrize("value", ["abc", "inf", "-inf", "nan"])
def test_parse_decimal_string_with_unaccepted_input(value):
    with pytest.raises(decimal.InvalidOperation):
        parse_decimal_string(value)
