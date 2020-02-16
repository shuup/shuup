# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import decimal

from shuup.core.fields import MONEY_FIELD_DECIMAL_PLACES


def ensure_decimal_places(value):
    return value.quantize(decimal.Decimal(".1") ** MONEY_FIELD_DECIMAL_PLACES)
