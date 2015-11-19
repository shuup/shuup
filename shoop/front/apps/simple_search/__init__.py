# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import shoop.apps


class AppConfig(shoop.apps.AppConfig):
    name = __name__
    verbose_name = "Shoop Frontend - Simple Search"
    label = "shoop_front.simple_search"

    provides = {
        "front_urls": [
            __name__ + ".urls:urlpatterns"
        ],
        "front_template_helper_namespace": [
            __name__ + ".template_helpers:TemplateHelpers"
        ]
    }


default_app_config = __name__ + ".AppConfig"
