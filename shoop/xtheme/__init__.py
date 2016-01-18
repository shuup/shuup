# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.apps import AppConfig
from shoop.utils import update_module_attributes

from ._theme import (
    get_current_theme, get_theme_by_identifier, set_current_theme, Theme
)
from .plugins._base import Plugin, templated_plugin_factory, TemplatedPlugin

__all__ = [
    "Plugin",
    "TemplatedPlugin",
    "Theme",
    "get_current_theme",
    "get_theme_by_identifier",
    "set_current_theme",
    "templated_plugin_factory"
]


class XThemeAppConfig(AppConfig):
    name = "shoop.xtheme"
    verbose_name = "Shoop Extensible Theme Engine"
    label = "shoop_xtheme"

    provides = {
        "front_urls_pre": [__name__ + ".urls:urlpatterns"],
        "xtheme_plugin": [
            "shoop.xtheme.plugins.text:TextPlugin"
        ],
        "admin_module": [
            "shoop.xtheme.admin_module:XthemeAdminModule"
        ]
    }


default_app_config = "shoop.xtheme.XThemeAppConfig"

update_module_attributes(__all__, __name__)
