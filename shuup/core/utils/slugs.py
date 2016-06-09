# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.utils.text import force_text, slugify


def generate_multilanguage_slugs(object, name_getter, slug_length=128):
    original_language = object.get_current_language()
    try:
        for language_code, language_name in settings.LANGUAGES:
            object.set_current_language(language_code)
            name = force_text(name_getter(object))
            if name:
                slug = slugify(name)
            else:
                slug = None
            object.slug = (slug[:slug_length] if slug else None)
        object.save_translations()
    finally:
        object.set_current_language(original_language)
