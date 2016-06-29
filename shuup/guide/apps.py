# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import shuup.apps


class AppConfig(shuup.apps.AppConfig):
    name = "shuup.guide"
    verbose_name = "Shuup Guide"
    provides = {
        "admin_module": [
            "shuup.guide.admin_module:GuideAdminModule"
        ],
    }
