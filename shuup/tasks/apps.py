# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import shuup.apps


class AppConfig(shuup.apps.AppConfig):
    name = "shuup.tasks"
    label = "shuup_tasks"
    provides = {
        "admin_module": [
            "shuup.tasks.admin_module.TaskAdminModule",
            "shuup.tasks.admin_module.TaskTypeAdminModule"
        ]
    }
