# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.utils.translation import get_language_info, ugettext


def get_language_choices():
    """
    Returns a list of the available language choices, e.g.:
        [("en", "English", "English"])

    :rtype iterable[(str, str, str)]
    """
    languages = []
    for code, name in settings.LANGUAGES:
        lang_info = get_language_info(code)
        name_in_current_lang = ugettext(name)
        local_name = lang_info["name_local"]
        languages.append((code, name_in_current_lang, local_name))
    return languages
