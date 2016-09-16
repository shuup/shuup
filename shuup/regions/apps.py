# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import shuup.apps


class AppConfig(shuup.apps.AppConfig):
    name = "shuup.regions"
    provides = {
        "xtheme_resource_injection": [
            "shuup.regions.resources:add_front_resources",
        ],
    }
