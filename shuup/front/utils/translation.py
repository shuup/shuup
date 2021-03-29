# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.utils.translation import get_language_info, ugettext, ugettext_lazy as _

from shuup import configuration

FRONT_AVAILABLE_LANGUAGES_CONFIG_KEY = "front:available_languages"


def get_language_choices(shop=None):
    """
    Returns a list of the available language choices, e.g.:
        [("en", "English", "English"])

    If a shop is passed, the languages will be filtered by those
    enabled for that shop.

    :rtype iterable[(str, str, str)]
    """
    available_languages = []
    languages = []

    if shop:
        available_languages = configuration.get(shop, FRONT_AVAILABLE_LANGUAGES_CONFIG_KEY)
        if available_languages:
            available_languages = available_languages.split(",")

    for code, name in settings.LANGUAGES:
        if available_languages and code not in available_languages:
            continue

        lang_info = get_language_info(code)
        name_in_current_lang = ugettext(name)
        local_name = lang_info["name_local"]
        languages.append((code, name_in_current_lang, local_name))
    return languages


def set_shop_available_languages(shop, languages):
    available_codes = [code for code, name in settings.LANGUAGES]

    # validate languages
    for language in languages:
        if language not in available_codes:
            msg = _("`{language_code}` is an invalid language code.").format(language_code=language)
            raise ValueError(msg)

    configuration.set(shop, FRONT_AVAILABLE_LANGUAGES_CONFIG_KEY, ",".join(languages))


def get_shop_available_languages(shop):
    available_languages = configuration.get(shop, FRONT_AVAILABLE_LANGUAGES_CONFIG_KEY, "")
    if available_languages:
        return available_languages.split(",")
    return []
