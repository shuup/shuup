# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import django.conf

from shoop.apps import AppConfig
from shoop.apps.settings import validate_templates_configuration


class ShoopFrontAppConfig(AppConfig):
    name = "shoop.front"
    verbose_name = "Shoop Frontend"
    label = "shoop_front"

    provides = {
        "admin_module": [
            "shoop.front.admin_module.BasketAdminModule",
        ],
        "notify_event": [
            "shoop.front.notify_events:OrderReceived"
        ]
    }

    def ready(self):
        validate_templates_configuration()
        if django.conf.settings.SHOOP_FRONT_INSTALL_ERROR_HANDLERS:
            from .error_handling import install_error_handlers
            install_error_handlers()


default_app_config = "shoop.front.ShoopFrontAppConfig"
