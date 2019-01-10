# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.apps import AppConfig


class AuthAppConfig(AppConfig):
    name = "shuup.front.apps.auth"
    verbose_name = "Shuup Frontend - User Authentication"
    label = "shuup_front.auth"

    provides = {
        "front_urls": [
            "shuup.front.apps.auth.urls:urlpatterns"
        ],
    }


default_app_config = "shuup.front.apps.auth.AuthAppConfig"
