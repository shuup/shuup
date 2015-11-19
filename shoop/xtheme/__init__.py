# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import shoop.apps

from .theme import Theme
from .plugins.base import Plugin, templated_plugin_factory

__all__ = ["Theme", "Plugin", "templated_plugin_factory"]


class AppConfig(shoop.apps.AppConfig):
    name = __name__
    verbose_name = "Shoop Extensible Theme Engine"
    label = "shoop_xtheme"

    provides = {
        "front_urls_pre": [__name__ + ".urls:urlpatterns"],
        "xtheme_plugin": [
            __name__ + ".plugins.text:TextPlugin"
        ],
        "admin_module": [
            __name__ + ".admin_module:XthemeAdminModule"
        ]
    }


default_app_config = __name__ + ".AppConfig"
