# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import babel
import babel.numbers
from babel.numbers import format_currency
from django.apps import apps
from django.utils import translation
from django.utils.lru_cache import lru_cache
from django.views.decorators.cache import cache_page
from django.views.i18n import javascript_catalog


@lru_cache()
def get_babel_locale(locale_string):
    """
    Parse a Django-format (dash-separated) locale string
    and return a Babel locale.

    This function is decorated with lru_cache, so executions
    should be cheap even if `babel.Locale.parse()` most definitely
    is not.

    :param locale_string: A locale string ("en-US", "fi-FI", "fi")
    :type locale_string: str
    :return: Babel Locale
    :rtype: babel.Locale
    """
    return babel.Locale.parse(locale_string, "-")


def get_current_babel_locale(fallback="en-US-POSIX"):
    """
    Get a Babel locale based on the thread's locale context.

    :param fallback:
      Locale to fallback to; set to None to raise an exception instead.
    :return: Babel Locale
    :rtype: babel.Locale
    """
    locale = get_babel_locale(locale_string=translation.get_language())
    if not locale:
        if fallback:
            locale = get_babel_locale(fallback)
        if not locale:
            raise ValueError(
                "Failed to get current babel locale (lang=%s)" %
                (translation.get_language(),))
    return locale


def format_percent(value, digits=0):
    locale = get_current_babel_locale()
    pattern = locale.percent_formats.get(None).pattern
    new_pattern = pattern.replace("0", "0." + (digits * "0"))
    return babel.numbers.format_percent(value, new_pattern, locale)


def format_money(amount, digits=None, widen=0, locale=None):
    """
    Format a Money object in the given locale.

    If neither digits or widen is passed, the preferred number of digits for
    the amount's currency is used.

    :param amount: The Money object to format
    :type amount: Money
    :param digits: How many digits to format the currency with.
    :type digits: int|None
    :param widen: How many digits to widen any existing decimal width with.
    :type widen: int|None
    :param locale: Locale object or locale identifier
    :type locale: Locale|str
    :return: Formatted string
    :rtype: str
    """
    if not locale:
        loc = get_current_babel_locale()
    else:
        loc = get_babel_locale(locale)

    if widen == 0 and digits is None:  # No special treatment required; format with the currency's digits.
        return format_currency(amount.value, amount.currency, locale=loc, currency_digits=True)

    pattern = loc.currency_formats["standard"].pattern

    # pattern is a formatting string.  Couple examples:
    # '¤#,##0.00', '#,##0.00\xa0¤', '\u200e¤#,##0.00', and '¤#0.00'

    if digits is not None:
        pattern = pattern.replace(".00", "." + (digits * "0"))
    if widen:
        pattern = pattern.replace(".00", ".00" + (widen * "0"))

    return format_currency(amount.value, amount.currency, pattern, loc, currency_digits=False)


def get_language_name(language_code):
    """
    Get a language's name in the currently active locale.

    :param language_code: Language code (possibly with an added script suffix (zh_Hans, zh-Hans))
    :type language_code: str
    :return: The language name, or the code if the language couldn't be derived.
    :rtype: str
    """
    try:
        lang_dict = get_current_babel_locale().languages
    except (AttributeError, ValueError):  # The locale lookup failed,
        return language_code  # so return the code as-is.
    for option in (
        language_code,
        str(language_code).replace("-", "_"),
    ):
        if option in lang_dict:
            return lang_dict[option]
    return language_code


@cache_page(3600)
def javascript_catalog_all(request, domain='djangojs'):
    """
    Get JavaScript message catalog for all apps in INSTALLED_APPS.
    """
    all_apps = [x.name for x in apps.get_app_configs()]
    return javascript_catalog(request, domain, all_apps)
