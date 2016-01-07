# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.apps import AppConfig


class AuthAppConfig(AppConfig):
    name = "shoop.front.apps.auth"
    verbose_name = "Shoop Frontend - User Authentication"
    label = "shoop_front.auth"

    provides = {
        "front_urls": [
            "shoop.front.apps.auth.urls:urlpatterns"
        ],
    }


default_app_config = "shoop.front.apps.auth.AuthAppConfig"
