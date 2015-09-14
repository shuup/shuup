# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
"""
A Bootstrap-powered default theme for Shoop.
"""
from shoop.apps import AppConfig
from shoop.xtheme.theme import Theme


class DefaultTheme(Theme):
    identifier = "shoop.themes.default_theme"
    name = "Shoop Default Theme"
    template_dir = "default/"


class DefaultThemeAppConfig(AppConfig):
    name = "shoop.themes.default_theme"
    verbose_name = DefaultTheme.name
    label = "shoop.themes.default_theme"
    provides = {
        "xtheme": "shoop.themes.default_theme:DefaultTheme"
    }


default_app_config = "shoop.themes.default_theme.DefaultThemeAppConfig"
