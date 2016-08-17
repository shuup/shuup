# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.core.signals import setting_changed

import pytest
from shuup.apps.provides import clear_provides_cache
from shuup.utils.importing import clear_load_cache
from shuup.xtheme.testing import override_current_theme_class


def clear_caches(setting, **kwargs):
    clear_load_cache()
    if setting == "INSTALLED_APPS":
        clear_provides_cache()


def pytest_configure(config):
    setting_changed.connect(clear_caches, dispatch_uid="shuup_test_clear_caches")
    settings.SHUUP_TELEMETRY_ENABLED = False


def pytest_runtest_call(item):
    # All tests are run with a theme override `shuup.themes.classic_gray.ClassicGrayTheme`.
    # To un-override, use `with override_current_theme_class()` (no arguments to re-enable database lookup)
    from shuup.themes.classic_gray.theme import ClassicGrayTheme
    item.session._theme_overrider = override_current_theme_class(ClassicGrayTheme)
    item.session._theme_overrider.__enter__()


def pytest_runtest_teardown(item, nextitem):
    if hasattr(item.session, "_theme_overrider"):
        item.session._theme_overrider.__exit__(None, None, None)
        del item.session._theme_overrider


@pytest.fixture(scope="session")
def splinter_make_screenshot_on_failure():
    return False
