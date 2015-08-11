# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.signals import setting_changed
from shoop.apps.provides import clear_provides_cache
from shoop.utils.importing import clear_load_cache
from shoop.xtheme.theme import override_current_theme_class


def clear_caches(setting, **kwargs):
    clear_load_cache()
    if setting == "INSTALLED_APPS":
        clear_provides_cache()


def pytest_configure(config):
    setting_changed.connect(clear_caches, dispatch_uid="shoop_test_clear_caches")


def pytest_runtest_call(item):
    # All tests are run with a default theme override `shoop.themes.default_theme.DefaultTheme`.
    # To un-override, use `with override_current_theme_class()` (no arguments to re-enable database lookup)
    from shoop.themes.default_theme import DefaultTheme
    item.session._theme_overrider = override_current_theme_class(DefaultTheme)
    item.session._theme_overrider.__enter__()


def pytest_runtest_teardown(item, nextitem):
    if hasattr(item.session, "_theme_overrider"):
        item.session._theme_overrider.__exit__(None, None, None)
        del item.session._theme_overrider
