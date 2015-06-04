# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from decimal import Decimal
from django.test.utils import override_settings
from django.utils import translation
from shoop.core.templatetags.shoop_common import percent, number, home_currency


def test_number_formatters():
    with override_settings(SHOOP_HOME_CURRENCY="USD"):
        with translation.override("en-US"):
            assert percent(Decimal("0.38")) == "38%"
            assert number(Decimal("38.00000")) == "38"
            assert number(Decimal("38.05000")) == "38.05"
            assert home_currency(Decimal("29.99")) == "$29.99"
        with translation.override("fi-FI"):
            assert percent(Decimal("0.38")) == "38\xa0%"
            assert number(Decimal("38.00000")) == "38"
            assert number(Decimal("38.05000")) == "38,05"
            assert home_currency(Decimal("29.99")) == "29,99\xa0$"
