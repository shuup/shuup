# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from datetime import date
from json import dumps as json_dump

from babel.dates import format_date, format_datetime, format_time
from babel.numbers import format_decimal
from django.utils.safestring import mark_safe
from django.utils.timezone import localtime
from django_jinja import library
from jinja2.runtime import Undefined

from shoop.utils.i18n import (
    format_money, format_percent, get_current_babel_locale
)
from shoop.utils.serialization import ExtendedJSONEncoder


@library.filter
def money(amount, digits=None, widen=0):
    """
    Format money amount according to current locale settings.

    :param amount: Money or Price object to format
    :type amount: shoop.utils.money.Money
    :param digits: Number of digits to use, by default use locale's default
    :type digits: int|None
    :param widen:
      Number of extra digits to add; for formatting with additional
      precision, e.g. ``widen=3`` will use 5 digits instead of 2
    :type widen: int
    :return: Formatted string representing the given amount
    :rtype: str
    """
    return format_money(amount, digits, widen)


@library.filter
def percent(value, ndigits=0):
    return format_percent(value, ndigits)


@library.filter
def number(value):
    return format_decimal(value, locale=get_current_babel_locale())


@library.filter
def datetime(value, kind="datetime", format="medium", tz=True):
    """
    Format a datetime for human consumption.

    The currently active locale's formatting rules are used.  The output
    of this function is probably not machine-parseable.

    :param value: datetime object to format
    :type value: datetime.datetime

    :param kind: Format as 'datetime', 'date' or 'time'
    :type kind: str

    :param format:
      Format specifier or one of 'full', 'long', 'medium' or 'short'
    :type format: str

    :param tz:
      Convert to current or given timezone. Accepted values are:

         True (default)
             convert to currently active timezone (as reported by
             :func:`django.utils.timezone.get_current_timezone`)
         False (or other false value like empty string)
             do no convert to any timezone (use UTC)
         Other values (as str)
             convert to given timezone (e.g. ``"US/Hawaii"``)
    :type tz: bool|str
    """

    locale = get_current_babel_locale()

    if type(value) is date:  # Not using isinstance, since `datetime`s are `date` too.
        # We can't do any TZ manipulation for dates, so just use `format_date` always
        return format_date(value, format=format, locale=locale)

    if tz:
        value = localtime(value, (None if tz is True else tz))

    if kind == "datetime":
        return format_datetime(value, format=format, locale=locale)
    elif kind == "date":
        return format_date(value, format=format, locale=locale)
    elif kind == "time":
        return format_time(value, format=format, locale=locale)
    else:
        raise ValueError("Unknown `datetime` kind: %r" % kind)


@library.filter(name="json")
def json(value):
    if isinstance(value, Undefined):
        value = None
    return mark_safe(json_dump(value, cls=ExtendedJSONEncoder))
