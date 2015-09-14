# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from shoop.apps import AppConfig
from shoop.xtheme.theme import Theme


class ClassicGrayTheme(Theme):
    identifier = "shoop.themes.classic_gray"
    name = "Shoop Classic Gray Theme"
    author = "Juha Kujala"
    template_dir = "classic_gray/"

    def get_view(self, view_name):
        import shoop.themes.classic_gray.views as views
        return getattr(views, view_name, None)


class ClassicGrayThemeAppConfig(AppConfig):
    name = "shoop.themes.classic_gray"
    verbose_name = ClassicGrayTheme.name
    label = "shoop.themes.classic_gray"
    provides = {
        "xtheme": "shoop.themes.classic_gray:ClassicGrayTheme",
        "xtheme_plugin": [
            "shoop.themes.classic_gray.plugins:ProductHighlightPlugin",
        ]
    }


default_app_config = "shoop.themes.classic_gray.ClassicGrayThemeAppConfig"
