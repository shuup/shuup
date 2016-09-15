# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
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

