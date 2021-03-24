# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import datetime
import mock
import pytest
import pytz

from shuup.reports.forms import DateRangeChoices
from shuup.reports.utils import parse_date_range_preset
from shuup.utils import i18n


def test_parse_date_range_presets():
    locale = i18n.get_current_babel_locale()

    def local_now():
        return datetime.datetime(2017, 12, 4, 17, 1, tzinfo=pytz.UTC)

    with mock.patch("shuup.utils.dates.local_now", side_effect=local_now):
        start, end = parse_date_range_preset(DateRangeChoices.TODAY)
        assert start == local_now().replace(hour=0, minute=0, second=0)
        assert end == local_now()

        start, end = parse_date_range_preset(DateRangeChoices.RUNNING_WEEK)
        assert start == local_now().replace(month=11, day=27, hour=0, minute=0, second=0)
        assert end == local_now()

        start, end = parse_date_range_preset(DateRangeChoices.RUNNING_MONTH)
        assert start == local_now().replace(month=11, day=4, hour=0, minute=0, second=0)
        assert end == local_now()

        assert local_now().weekday() == locale.first_week_day
        start, end = parse_date_range_preset(DateRangeChoices.THIS_WEEK)
        assert start == local_now().replace(hour=0, minute=0, second=0)
        assert end == local_now()

        start, end = parse_date_range_preset(DateRangeChoices.THIS_MONTH)
        assert start == local_now().replace(month=12, day=1, hour=0, minute=0, second=0)
        assert end == local_now()

        start, end = parse_date_range_preset(DateRangeChoices.THIS_YEAR)
        assert start == local_now().replace(month=1, day=1, hour=0, minute=0, second=0)
        assert end == local_now()

        start, end = parse_date_range_preset(DateRangeChoices.ALL_TIME)
        assert start == local_now().replace(year=2000, hour=0, minute=0, second=0)
        assert end == local_now()


@pytest.mark.parametrize("locale", ["en-US", "fi-FI"])
def test_parse_date_range_presets_running_week(locale):
    def get_locale():
        return i18n.get_babel_locale(locale)

    def monday():
        return datetime.datetime(2017, 12, 4, 17, 1, tzinfo=pytz.UTC)

    def tuesday():
        return datetime.datetime(2017, 12, 5, 17, 1, tzinfo=pytz.UTC)

    def wednesday():
        return datetime.datetime(2017, 12, 6, 17, 1, tzinfo=pytz.UTC)

    def thursday():
        return datetime.datetime(2017, 12, 7, 17, 1, tzinfo=pytz.UTC)

    def friday():
        return datetime.datetime(2017, 12, 8, 17, 1, tzinfo=pytz.UTC)

    def saturday():
        return datetime.datetime(2017, 12, 9, 17, 1, tzinfo=pytz.UTC)

    with mock.patch("shuup.utils.i18n.get_current_babel_locale", side_effect=get_locale):
        for local_now in [monday, tuesday, wednesday, thursday, friday, saturday]:
            with mock.patch("shuup.utils.dates.local_now", side_effect=local_now):
                start, end = parse_date_range_preset(DateRangeChoices.THIS_WEEK)
                assert start == local_now().replace(day=(3 if locale == "en-US" else 4), hour=0, minute=0, second=0)
                assert start.weekday() == get_locale().first_week_day
                assert end == local_now()
