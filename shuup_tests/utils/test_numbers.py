# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import decimal
from decimal import Decimal

import pytest

from shuup.utils.numbers import parse_decimal_string


@pytest.mark.parametrize("input_val, expected_val", [
    (0.0, Decimal('0.0')),
    (1.1, Decimal('1.1')),
    (-1.1, Decimal('-1.1')),
    (1e10, Decimal('10000000000')),
    (1e10, Decimal('1e10')),
    (1e-10, Decimal('0.0000000001')),
    (1e-10, Decimal('1e-10'))
])
def test_parse_decimal_string_with_float_input(input_val, expected_val):
    result = parse_decimal_string(input_val)
    assert result == expected_val


def test_parse_decimal_string_with_normal_input():
    assert parse_decimal_string('42') == Decimal(42)
    assert parse_decimal_string('0') == Decimal(0)
    assert parse_decimal_string(3.5) == Decimal('3.5')
    assert parse_decimal_string(-5) == Decimal(-5)
    assert parse_decimal_string('-5') == Decimal(-5)


def test_parse_decimal_string_with_dirty_input():
    assert parse_decimal_string('1e12') == Decimal(112)
    assert parse_decimal_string('foo1bar 1x2') == Decimal(112)
    assert parse_decimal_string('4a bc2def 8g.h5') == Decimal('428.5')
    assert parse_decimal_string(float('inf')) == Decimal('inf')
    assert parse_decimal_string(float('-inf')) == Decimal('-inf')
    assert str(parse_decimal_string(float('nan'))) == str(Decimal('nan'))
    assert parse_decimal_string('') == Decimal(0)
    assert parse_decimal_string(' ') == Decimal(0)


@pytest.mark.parametrize("value", ['abc', 'inf', '-inf', 'nan'])
def test_parse_decimal_string_with_unaccepted_input(value):
    with pytest.raises(decimal.InvalidOperation):
        parse_decimal_string(value)
