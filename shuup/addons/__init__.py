# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.apps import AppConfig

from .manager import add_enabled_addons

__all__ = ["add_enabled_addons"]


class ShuupAddonsAppConfig(AppConfig):
    name = "shuup.addons"
    verbose_name = "Shuup Addons"
    label = "shuup_addons"

    provides = {
        "admin_module": [
            "shuup.addons.admin_module:AddonModule",
        ]
    }


default_app_config = "shuup.addons.ShuupAddonsAppConfig"
