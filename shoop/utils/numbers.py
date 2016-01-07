# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import re
from decimal import Decimal, ROUND_HALF_EVEN

import six

from ._united_decimal import UnitedDecimal, UnitMixupError

__all__ = [
    "UnitedDecimal",
    "UnitMixupError",
    "bankers_round",
    "strip_non_float_chars",
    "parse_decimal_string",
    "try_parse_decimal_string",
    "get_string_sort_order",
]

quant_cache = {}


def bankers_round(value, ndigits=0):
    if isinstance(value, float):
        value = Decimal(str(value))
    elif not isinstance(value, Decimal):
        value = Decimal(value)
    # We can cache the quantizers...
    quantizer = quant_cache.get(ndigits)
    if quantizer is None:
        quantizer = quant_cache[ndigits] = Decimal(10) ** (-int(ndigits))
    return value.quantize(quantizer, rounding=ROUND_HALF_EVEN)


def strip_non_float_chars(s):
    """ Strips characters that aren't part of normal floats. """
    return re.sub("[^-+0123456789.]+", "", six.text_type(s))


def parse_decimal_string(s):
    """
    Parse decimals with "best effort".

    Parses a string (or unicode) that may be embellished
    with spaces and other weirdness into the most probable Decimal.

    :param s: Input value
    :type s: str
    :return: Decimal
    :rtype: Decimal
    """

    if isinstance(s, six.integer_types) or isinstance(s, Decimal):
        return Decimal(s)

    if isinstance(s, float):
        s = str(s)

    s = s.strip().replace(" ", "")  # Also 500 000.0 would be.. well, 500 :D

    if not s:
        return Decimal(0)

    if "," in s:  # 500000,0? D:
        if "." in s:  # Taking care of cases like 500,000.00
            s = s.replace(",", "")
            # There we go, we have 500000.0 already
        else:
            s = s.replace(",", ".")
            # And there, it's a 500000.0

    # Then clean up the rest and pray for DEITY HERE
    return Decimal(strip_non_float_chars(s.strip()))


def try_parse_decimal_string(s):
    try:
        return parse_decimal_string(s)
    except:
        return None


GARMENT_SIZES = ("XXXS", "XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL")


def get_string_sort_order(s):
    """
    Return a sorting order value for a string that contains a garment size.

    :param s: Input value (string or number)
    :type s: str
    :return: Sorting tuple
    :rtype: tuple
    """
    # See if it's one of the predefined sizes
    for i, size in enumerate(GARMENT_SIZES):
        if size in s:
            return (10 + i, s)

    try:  # If not, see if it looks enough like a decimal
        return (5, parse_decimal_string(s))
    except:  # Otherwise just sort as a string
        return (1, s)
