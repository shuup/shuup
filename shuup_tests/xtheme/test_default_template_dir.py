# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.test import override_settings

from shuup.core import cache
from shuup.testing.factories import get_default_shop
from shuup.testing.themes import ShuupTestingTheme, ShuupTestingThemeWithCustomBase
from shuup.utils.django_compat import reverse
from shuup.xtheme.testing import override_current_theme_class
from shuup_tests.utils import SmartClient


@pytest.mark.django_db
def test_theme_without_default_template_dir():
    with override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "test_configuration_cache",
            }
        }
    ):
        cache.init_cache()

        with override_current_theme_class(ShuupTestingTheme, get_default_shop()):
            c = SmartClient()
            soup = c.soup(reverse("shuup:index"))
            assert "Simple base for themes to use" not in soup
            assert "Welcome to test Shuup!" in soup.find("div", {"class": "page-content"}).text


@pytest.mark.django_db
def test_theme_with_default_template_dir():
    with override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "test_configuration_cache",
            }
        }
    ):
        cache.init_cache()
        get_default_shop()
        with override_current_theme_class(ShuupTestingThemeWithCustomBase, get_default_shop()):
            c = SmartClient()
            soup = c.soup(reverse("shuup:index"))
            assert "Simple base for themes to use" in soup.find("h1").text
            assert "Welcome to test Shuup!" in soup.find("h1").text
