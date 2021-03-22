# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.apps import apps
from django.test import override_settings

from shuup.core import MissingSettingException


@pytest.mark.parametrize(
    "setting_key, value, should_raise",
    [
        ("PARLER_DEFAULT_LANGUAGE_CODE", None, True),
        ("PARLER_DEFAULT_LANGUAGE_CODE", False, True),
        ("PARLER_DEFAULT_LANGUAGE_CODE", "", True),
        ("PARLER_DEFAULT_LANGUAGE_CODE", "en", False),
        ("PARLER_LANGUAGES", None, True),
        ("PARLER_LANGUAGES", False, True),
        ("PARLER_LANGUAGES", "", True),
        ("PARLER_LANGUAGES", {}, True),
        ("PARLER_LANGUAGES", {None: [1, 2]}, False),
        ("PARLER_LANGUAGES", {"en": [1, 2]}, False),
    ],
)
@pytest.mark.django_db
def test_parler_language_code(setting_key, value, should_raise):
    kwargs = {setting_key: value}
    with override_settings(**kwargs):
        if should_raise:
            with pytest.raises(MissingSettingException):
                apps.get_app_config("shuup").ready()
