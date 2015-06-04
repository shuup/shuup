# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django.conf import settings


ZERO_DECIMAL_CURRENCIES = (
    # https://support.stripe.com/questions/which-zero-decimal-currencies-does-stripe-support
    "BIF", "CLP", "DJF", "GNF", "JPY", "KMF", "KRW", "MGA", "PYG", "RWF", "VND", "VUV", "XAF", "XOF", "XPF"
)


def get_amount_info(total):
    currency = settings.SHOOP_HOME_CURRENCY
    multiplier = (1 if currency in ZERO_DECIMAL_CURRENCIES else 100)
    return {
        "currency": currency,
        "amount": int(total * multiplier),
    }
