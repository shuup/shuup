# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

import decimal
from collections import defaultdict

import babel.core

_cache = None
_default = None


def get_precision(currency):
    """
    Get precisision for given currency from Babel.

    :type currency: str
    :param currency: Currency code as 3-letter string (ISO-4217)

    :rtype: decimal.Decimal
    :return: Precision value for given currency code
    """
    global _cache
    if _cache is None:
        _cache = _generate_cache()
    return _cache[currency]


def _generate_cache():
    currency_fractions = babel.core.get_global('currency_fractions')
    values = {
        currency: decimal.Decimal('0.1') ** data[0]
        for (currency, data) in currency_fractions.items()
    }
    default = values.pop('DEFAULT')
    cache = defaultdict(lambda: default)
    cache.update(values)
    return cache
