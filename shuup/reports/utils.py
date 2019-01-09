# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import datetime

import six

from shuup.utils import dates, i18n, iterables

ERROR_MESSAGE = "Error fetching data"
NO_DATA_MESSAGE = "No results"


def get_empty_data(schema, data, message):
    keys = [s.get("key") for s in schema]
    return_data = {}
    for key in keys:
        return_data[key] = message
    return {
        "data": [return_data],
        "start": data["start"],
        "end": data["end"],
    }


def get_error_data(schema, sales_data):
    if sales_data.get("data") == "error":
        return get_empty_data(schema, sales_data, ERROR_MESSAGE)
    if not sales_data.get("data")[0]:
        return get_empty_data(schema, sales_data, NO_DATA_MESSAGE)


def get_first_day_of_the_current_week(today_start):
    locale = i18n.get_current_babel_locale()
    first_day_of_the_week = today_start
    if today_start.weekday() == locale.first_week_day:
        return first_day_of_the_week

    def get_prospect(i):
        return (today_start - datetime.timedelta(days=i))

    return iterables.first([get_prospect(i) for i in range(1, 7) if get_prospect(i).weekday() == locale.first_week_day])


def parse_date_range_preset(value):
    from shuup.reports.forms import DateRangeChoices
    now = dates.local_now()
    today_start = now.replace(hour=0, minute=0, second=0)
    if value == DateRangeChoices.TODAY:
        return (today_start, now)
    elif value == DateRangeChoices.RUNNING_WEEK:
        return (today_start - datetime.timedelta(days=7), now)
    elif value == DateRangeChoices.THIS_WEEK:
        return (get_first_day_of_the_current_week(today_start), now)
    elif value == DateRangeChoices.RUNNING_MONTH:
        return (today_start - datetime.timedelta(days=30), now)
    elif value == DateRangeChoices.THIS_MONTH:
        return (today_start.replace(day=1), now)
    elif value == DateRangeChoices.THIS_YEAR:
        return (today_start.replace(day=1, month=1), now)
    elif value == DateRangeChoices.ALL_TIME:
        return (today_start.replace(year=2000), now)


def parse_date_range(value):
    output = parse_date_range_preset(value)
    if output:
        return output

    if isinstance(value, six.string_types):
        value = value.strip()
        if ".." in value:
            start, end = value.split("..", 1)
        elif value.count("-") == 1:
            start, end = value.split("-", 1)
        else:
            start, end = value.split(None, 1)
    elif isinstance(value, (list, tuple)):
        start, end = value[:2]
    else:
        raise ValueError("Can't split date range: %r" % value)
    date_range = (dates.try_parse_datetime(start), dates.try_parse_datetime(end))
    if any(p is None for p in date_range):
        raise ValueError("Invalid date range: %r (parsed as %r)" % (value, date_range))
    return date_range
