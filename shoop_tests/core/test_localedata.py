# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import datetime

import babel
import pytest
from babel.dates import format_date

from shoop.utils.dates import get_year_and_month_format


@pytest.mark.parametrize("locale_name,expected", [
    ("fi_FI", "maalis 1980"),
    ("en_US", "Mar 1980"),
    ("sv", "mars 1980"),
])
def test_year_and_month(locale_name, expected):
    locale = babel.Locale.parse(locale_name)
    formatted = format_date(
        datetime.date(1980, 3, 1),
        format=get_year_and_month_format(locale),
        locale=locale
    )
    assert formatted == expected
