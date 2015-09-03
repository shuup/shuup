# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.apps import AppConfig


class XThemeAppConfig(AppConfig):
    name = "shoop.xtheme"
    verbose_name = "Shoop Extensible Theme Engine"
    label = "shoop_xtheme"

    provides = {
        "xtheme_plugin": [
            "shoop.xtheme.plugins.text:TextPlugin"
        ]
    }


default_app_config = "shoop.xtheme.XThemeAppConfig"
