# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import shoop.apps
from .manager import add_enabled_addons

__all__ = ["add_enabled_addons"]


class AppConfig(shoop.apps.AppConfig):
    name = __name__
    verbose_name = "Shoop Addons"
    label = "shoop_addons"

    provides = {
        "admin_module": [
            __name__ + ".admin_module:AddonModule",
        ]
    }


default_app_config = __name__ + ".AppConfig"
