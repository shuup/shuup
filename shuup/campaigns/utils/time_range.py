# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import datetime

from django.utils import timezone


def is_in_time_range(date, hour_start, hour_end, valid_weekdays):
    """
    Help util for hour conditions in basket and catalog campaigns.

    Since the start and end hour is saved to database without any
    timezone information we need to get current hour not in UTC
    but shop local time.

    :type date: datetime.datetime
    :type hour_start: django.db.models.TimeField|datetime.time
    :type hour_end: django.db.models.TimeField|datetime.time
    :type valid_weekdays: list(int)
    :return: Whether the current time is in time range and correct weekday
    :rtype: bool
    """
    current_local_dt = timezone.localtime(date)
    current_local_weekday = current_local_dt.date().weekday()

    start_datetime = timezone.get_current_timezone().localize(
        datetime.datetime.combine(
            current_local_dt.date(), hour_start
        )
    )
    end_datetime = timezone.get_current_timezone().localize(
        datetime.datetime.combine(
            current_local_dt.date(), hour_end
        )
    )

    valid_date_ranges = []
    if hour_start > hour_end:
        end_datetime += datetime.timedelta(days=1)

        if current_local_weekday in valid_weekdays:
            valid_date_ranges.append((start_datetime, end_datetime))
        else:
            valid_date_ranges.append(
                (start_datetime - datetime.timedelta(days=1), end_datetime - datetime.timedelta(days=1))
            )
            valid_weekdays.append(current_local_weekday)
    else:
        valid_date_ranges.append((start_datetime, end_datetime))

    if current_local_weekday not in valid_weekdays:
        return False

    return any([(start <= current_local_dt < end) for (start, end) in valid_date_ranges])
