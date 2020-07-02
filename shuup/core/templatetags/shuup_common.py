# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
"""
Common helpers for Shuup templates.

.. note::

   In addition to these, also the price rendering tags from
   `shuup.core.templatetags.prices` module are available.
"""

from __future__ import unicode_literals

from datetime import date
from json import dumps as json_dump

import bleach
from babel.dates import format_date, format_datetime, format_time
from babel.numbers import format_decimal
from django.conf import settings
from django.utils import translation
from django.utils.safestring import mark_safe
from django.utils.timezone import localtime
from django_jinja import library
from jinja2 import Undefined
from jinja2.utils import contextfunction

from shuup.utils.i18n import (
    format_money, format_percent, get_current_babel_locale
)
from shuup.utils.serialization import ExtendedJSONEncoder


@library.global_function
def get_language_choices():
    """
    Get language choices as code and text in two languages.

    :return:
      Available language codes as tuples (`code`, `name`, `local_name`)
      where `name` is in the currently active language, and `local_name`
      is in the language of the item.
    :rtype: Iterable[tuple[str,str,str]]
    """
    for (code, name) in settings.LANGUAGES:
        lang_info = translation.get_language_info(code)
        name_in_current_lang = translation.ugettext(name)
        local_name = lang_info["name_local"]
        yield (code, name_in_current_lang, local_name)


@library.filter
def money(amount, digits=None, widen=0):
    """
    Format money amount according to the current locale settings.

    :param amount: Money or Price object to format.
    :type amount: shuup.utils.money.Money
    :param digits: Number of digits to use, by default use locale's default.
    :type digits: int|None
    :param widen:
      Number of extra digits to add; for formatting with additional
      precision, e.g. ``widen=3`` will use 5 digits instead of the default 2.
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
    Format a `datetime` for human consumption.

    The currently active locale's formatting rules are used. The output
    of this function is probably not machine-parseable.

    :param value: datetime object to format
    :type value: datetime.datetime

    :param kind: Format as 'datetime', 'date' or 'time'.
    :type kind: str

    :param format:
      Format specifier or one of 'full', 'long', 'medium' or 'short'.
    :type format: str

    :param tz:
      Convert to current or given timezone. Accepted values are:

         True (default)
             convert to the currently active timezone (as reported by
             :func:`django.utils.timezone.get_current_timezone`)
         False (or other false value like empty string)
             do no convert to any timezone (use UTC)
         Other values (as str)
             convert to a given timezone (e.g. ``"US/Hawaii"``)
    :type tz: bool|str
    """

    locale = get_current_babel_locale()

    if type(value) is date:  # Not using isinstance, since `datetime`s are `date` too.
        # We can't do any TZ manipulation for dates, so just always use `format_date`
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
        raise ValueError("Error! Unknown `datetime` kind: %r." % kind)


@library.filter(name="json")
def json(value):
    if isinstance(value, Undefined):
        value = None
    return mark_safe(json_dump(value, cls=ExtendedJSONEncoder))


@library.filter
def safe_product_description(value):
    if isinstance(value, Undefined):
        return value
    if not settings.SHUUP_ADMIN_ALLOW_HTML_IN_PRODUCT_DESCRIPTION:
        value = bleach.clean(value, tags=[])
    return mark_safe(value)


@library.filter
def safe_vendor_description(value):
    if isinstance(value, Undefined):
        return value
    if not settings.SHUUP_ADMIN_ALLOW_HTML_IN_VENDOR_DESCRIPTION:
        value = bleach.clean(value, tags=[])
    return mark_safe(value)


@library.global_function
@contextfunction
def get_shop_configuration(context, name, default=None):
    """
    Get configuration variable value for the current shop.

    :type context: jinja2.runtime.Context
    :type name: str
    :type default: Any
    """
    from shuup import configuration
    return configuration.get(context.get("request").shop, name, default)


@library.global_function
def get_global_configuration(name, default=None):
    """
    Get global configuration variable value.

    :type name: str
    :type default: Any
    """
    from shuup import configuration
    return configuration.get(None, name, default)


@library.global_function
def get_shuup_version():
    from shuup import __version__
    return __version__


@library.global_function
def shuup_static(path):
    from shuup.core.utils.static import get_shuup_static_url
    return get_shuup_static_url(path)
