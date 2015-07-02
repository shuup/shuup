# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.exceptions import ImproperlyConfigured
from shoop.apps import AppConfig


class ShoopApiAppConfig(AppConfig):
    name = "shoop.api"
    verbose_name = "Shoop API"
    label = "shoop_api"
    required_installed_apps = (
        "rest_framework",
    )

    def ready(self):
        super(ShoopApiAppConfig, self).ready()
        from django.conf import settings
        rest_framework_config = getattr(settings, "REST_FRAMEWORK", None)
        if not (rest_framework_config and rest_framework_config.get("DEFAULT_PERMISSION_CLASSES")):
            raise ImproperlyConfigured(
                "`shoop.api` REQUIRES explicit configuration of `REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES']` "
                "in your settings file. This is to avoid all of your shop's orders being world-readable-and-writable."
            )


default_app_config = "shoop.api.ShoopApiAppConfig"
