# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import babel
import datetime
import pytest
from babel.dates import format_date

from shuup.utils.dates import get_year_and_month_format
from shuup.utils.i18n import format_money
from shuup.utils.money import Money


@pytest.mark.parametrize(
    "locale_name,expected",
    [
        ("fi_FI", "maalis 1980"),
        ("en_US", "Mar 1980"),
        ("sv", "mars 1980"),
    ],
)
def test_year_and_month(locale_name, expected):
    locale = babel.Locale.parse(locale_name)
    formatted = format_date(datetime.date(1980, 3, 1), format=get_year_and_month_format(locale), locale=locale)
    assert formatted == expected


def test_format_money():
    assert format_money(Money("3.6", "EUR"), locale="fi") == "3,60\xa0\u20ac"
    assert format_money(Money("3.6", "EUR"), widen=2, locale="fi") == "3,6000\xa0\u20ac"
    assert format_money(Money("3.6", "EUR"), digits=0, locale="fi") == "4\xa0\u20ac"
