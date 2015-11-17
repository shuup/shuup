# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings

import shoop.apps
from shoop.apps.settings import validate_templates_configuration


class AppConfig(shoop.apps.AppConfig):
    name = __name__
    verbose_name = "Shoop Frontend"
    label = "shoop_front"

    provides = {
        "admin_module": [
            __name__ + ".admin_module.BasketAdminModule",
        ],
        "notify_event": [
            __name__ + ".notify_events:OrderReceived"
        ]
    }

    def ready(self):
        validate_templates_configuration()

        if settings.SHOOP_FRONT_INSTALL_ERROR_HANDLERS:
            from .error_handling import install_error_handlers
            install_error_handlers()


default_app_config = __name__ + ".AppConfig"
