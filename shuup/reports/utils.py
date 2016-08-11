# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import datetime

import six
from django.utils import timezone

from shuup.utils.dates import try_parse_date

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


def parse_date_range_preset(value):
    from shuup.reports.forms import DateRangeChoices
    now = timezone.now()
    if value == DateRangeChoices.TODAY:
        midnight = now.replace(hour=0, minute=0, second=0)
        tomorrow = midnight + datetime.timedelta(days=1)
        return (midnight, tomorrow)
    if value == DateRangeChoices.RUNNING_WEEK:
        return (now - datetime.timedelta(days=7), now)
    if value == DateRangeChoices.RUNNING_MONTH:
        return (now - datetime.timedelta(days=30), now)
    if value == DateRangeChoices.THIS_MONTH:
        return (now.replace(day=1), now)
    if value == DateRangeChoices.THIS_YEAR:
        return (now.replace(day=1, month=1), now)
    if value == DateRangeChoices.ALL_TIME:
        return (now.replace(year=2000), now)


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
    date_range = (try_parse_date(start), try_parse_date(end))
    if any(p is None for p in date_range):
        raise ValueError("Invalid date range: %r (parsed as %r)" % (value, date_range))
    return date_range
