# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import datetime
import itertools
import time

import django
import six
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext

__all__ = ("parse_date", "parse_time", "try_parse_date", "try_parse_time", "try_parse_datetime")

_date_formats = (
    "%Y-%m-%d",
    "%Y%m%d",
    "%Y/%m/%d",
    "%d.%m.%y",
    "%d.%m.%Y",
    "%Y %m %d",
    "%m/%d/%Y",
)

_time_formats = (
    "%H:%M:%S",
    "%H:%M",
)

_datetime_formats = list(itertools.chain.from_iterable([
    ["{} %H:%M:%S".format(fmt) for fmt in _date_formats],
    ["{} %H:%M".format(fmt) for fmt in _date_formats]
]))

locale_year_and_month_formats = {
    # Sourced from the Unicode CLDR, version 27.1.
    # All locales not listed here use "MMM y".
    'be': 'LLL y',
    'bg': "MM.y 'г'.",
    'bs': 'MMM y.',
    'ca': 'LLL y',
    'cs': 'LLLL y',
    'dz': 'y སྤྱི་ཟླ་MMM',
    'eu': 'y MMM',
    'fi': 'LLL y',
    'fo': 'y MMM',
    'hr': 'LLL y.',
    'hu': 'y. MMM',
    'hy': 'yթ. LLL',
    'ja': 'y年M月',
    'ka': 'MMM, y',
    'kea': "MMM 'di' y",
    'ko': 'y년 MMM',
    'ky': "y-'ж'. MMM",
    'lt': 'y-MM',
    'lv': "y. 'g'. MMM",
    'mk': "MMM y 'г'.",
    'ml': 'y MMM',
    'mn': 'y MMM',
    'ne': 'y MMM',
    'os': 'LLL y',
    'pl': 'MM.y',
    'pt': 'MM/y',
    'ru': 'LLL y',
    'seh': "MMM 'de' y",
    'si': 'y MMM',
    'sk': 'LLLL y',
    'sr': 'MMM y.',
    'uk': 'LLL y',
    'uz': 'y MMM',
}


def _parse_date_str(value):
    value = value.strip()
    for fmt in _date_formats:
        try:
            return datetime.datetime.strptime(value, fmt).date()
        except Exception:
            pass
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f").date()
    except Exception:
        pass


def _parse_datetime_str(value):
    value = value.strip()
    for fmt in itertools.chain.from_iterable((_datetime_formats, _date_formats)):
        try:
            return datetime.datetime.strptime(value, fmt)
        except Exception:
            pass
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
    except Exception:
        pass


def _parse_time_str(value):
    value = value.strip()
    for fmt in _time_formats:
        try:
            return datetime.datetime.strptime(value, fmt).time()
        except Exception:
            pass
    return None


def parse_date(value):
    """
    Tries to make a date out of the value. If impossible, it raises an exception.

    :param value: A value of some kind.
    :return: Date
    :rtype: datetime.date
    :raise ValueError:
    """
    # This should be first since `datetime.datetime` is a subclass of `datetime.date`
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    elif isinstance(value, six.string_types):
        date = _parse_date_str(value)
        if not date:
            raise ValueError("Error! Unable to parse `%s` as date." % value)
        return date
    raise ValueError("Error! Unable to parse `%s` as date (unknown type)." % value)


def parse_datetime(value):
    """
    Tries to make a datetime out of the value. If impossible, it raises an exception.

    :param value: A value of some kind.
    :return: DateTime.
    :rtype: datetime.datetime
    :raise ValueError:
    """
    # This should be first since `datetime.datetime` is a subclass of `datetime.date`
    if isinstance(value, datetime.datetime):
        return value
    if isinstance(value, datetime.date):
        return datetime.datetime.combine(value, datetime.datetime.min.time())
    elif isinstance(value, six.string_types):
        date = _parse_datetime_str(value)
        if not date:
            raise ValueError("Error! Unable to parse `%s` as datetime." % value)
        return date
    raise ValueError("Error! Unable to parse `%s` as datetime (unknown type)." % value)


def parse_time(value):
    """
    Tries to make a time out of the value. If impossible, it raises an exception.

    :param value: A value of some kind.
    :return: Time.
    :rtype: datetime.time
    :raise ValueError:
    """
    if isinstance(value, datetime.time):
        return value
    if isinstance(value, datetime.datetime):
        return value.time()
    if isinstance(value, six.string_types):
        parsed_time = _parse_time_str(value)
        if not parsed_time:
            raise ValueError("Error! Unable to parse `%s` as date." % value)
        return parsed_time
    raise ValueError("Error! Unable to parse `%s` as date (unknown type)." % value)


def try_parse_datetime(value):
    """
    Tries to make a datetime out of the value. If impossible, returns None.

    :param value: A value of some kind.
    :return: Datetime.
    :rtype: datetime.datetime
    """
    if value is None:
        return None
    try:
        return parse_datetime(value)
    except ValueError:
        return None


def try_parse_date(value):
    """
    Tries to make a time out of the value. If impossible, returns None.

    :param value: A value of some kind.
    :return: Date.
    :rtype: datetime.date
    """
    if value is None:
        return None
    try:
        return parse_date(value)
    except ValueError:
        return None


def try_parse_time(value):
    """
    Tries to make a time out of the value. If impossible, returns None.

    :param value: A value of some kind.
    :return: Time.
    :rtype: datetime.time
    """
    if value is None:
        return None
    try:
        return parse_time(value)
    except ValueError:
        return None


def get_year_and_month_format(locale):
    """
    Get the Babel/Unicode format string for a "year and month" format
    for the given locale.

    Only the "language" part of the locale is taken into account here.

    :param locale: Babel locale.
    :type locale: babel.Locale
    :return: format string.
    :rtype: str
    """
    return locale_year_and_month_formats.get(locale.language.lower(), "MMM y")


def to_aware(date, time=datetime.time.min, tz=None):
    """
    Convert date or datetime to aware datetime.

    :type date: datetime.date|datetime.datetime
    :param date:
      Date or datetime object to convert.
    :type time: datetime.time
    :param time:
      Time value for supplementing dates to datetimes, default 0:00:00.
    :type tz: datetime.tzinfo|None
      Timezone to use, default ``timezone.get_current_timezone()``.
    :rtype: datetime.datetime
    :return:
      Converted aware datetime object.
    """
    if isinstance(date, datetime.datetime):
        if timezone.is_aware(date):
            return date
        return dst_safe_timezone_aware(date, tz)
    assert isinstance(date, datetime.date), '%r should be date' % (date,)
    combined = datetime.datetime.combine(date, time)
    return dst_safe_timezone_aware(combined, tz)


def dst_safe_timezone_aware(dt, tz=None):
    """
    Safely make datetime aware considering Daylight Saving Time (DST) cases.

    If `timezone.make_aware` raises `pytz.exceptions.NonExistentTimeError`,
    it means the time doesn't exist on that timezone it is probably DST.

    :type dt: datetime.datetime
    :param dt:
      Datetime object to make aware.
    :type tz: datetime.tzinfo|None
      Timezone to use, default ``timezone.get_current_timezone()``.
    :rtype: datetime.datetime
    :return:
      Converted aware datetime object.
    """
    from pytz.exceptions import NonExistentTimeError

    try:
        return timezone.make_aware(dt, timezone=tz)
    except NonExistentTimeError:
        if django.VERSION < (1, 9):
            # is_dst parameter is not available for Django 1.8
            if tz is None:
                tz = timezone.get_current_timezone()
            return tz.localize(dt, is_dst=True)

        return timezone.make_aware(dt, timezone=tz, is_dst=True)


def local_now(tz=None):
    """
    Get current time as aware datetime in local timezone.

    :type tz: datetime.tzinfo|None
      Timezone to use, default ``timezone.get_current_timezone()``
    :rtype: datetime.datetime
    """
    return timezone.localtime(to_aware(timezone.now()), timezone=tz)


def to_timestamp(date):
    """
    Get a UNIX timestamp from a date or datetime.

    :param datetime.date|datetime.datetime date: the datetime to convert to unix timestamp.
    :rtype float
    """
    return time.mktime(date.timetuple())


def to_datetime_range(start, end):
    for value in [start, end]:
        if not isinstance(value, datetime.date):
            raise TypeError("Error! Provided value `{!r}` is neither date nor datetime.".format(value))
    start_is_datetime = isinstance(start, datetime.datetime)
    end_is_datetime = isinstance(end, datetime.datetime)
    if start_is_datetime != end_is_datetime:
        raise TypeError("Error! Start and end must be of the same type: `{!r}` - `{!r}`."
                        .format(start, end))
    # Add +1 day to end if it's a date to make the range inclusive
    end_delta = datetime.timedelta(days=(1 if not end_is_datetime else 0))
    return (to_aware(start), to_aware(end) + end_delta)


class DurationRange(object):
    """
    Present duration range, min days to max days.
    """
    def __init__(self, min_duration, max_duration=None):
        assert isinstance(min_duration, datetime.timedelta)
        assert max_duration is None or (
            isinstance(max_duration, datetime.timedelta))
        assert max_duration is None or max_duration >= min_duration
        self.min_duration = min_duration
        self.max_duration = (max_duration if max_duration is not None
                             else min_duration)

    @classmethod
    def from_days(cls, min_days, max_days=None):
        return cls(
            datetime.timedelta(days=min_days),
            (datetime.timedelta(days=max_days)
             if max_days is not None else None))

    def __str__(self):
        if self.min_duration == self.max_duration:
            days = self.max_duration.days
            return ungettext("%s day", "%s days", days) % (days,)
        return _("%(min)s--%(max)s days") % {
            "min": self.min_duration.days, "max": self.max_duration.days}
