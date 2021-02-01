# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from shuup.apps import AppConfig


class ShuupNotifyAppConfig(AppConfig):
    name = "shuup.notify"
    verbose_name = "Shuup Notification Framework"
    label = "shuup_notify"
    provides = {
        "notify_condition": [
            "shuup.notify.conditions:LanguageEqual",
            "shuup.notify.conditions:BooleanEqual",
            "shuup.notify.conditions:IntegerEqual",
            "shuup.notify.conditions:TextEqual",
            "shuup.notify.conditions:Empty",
            "shuup.notify.conditions:NonEmpty",
        ],
        "notify_action": [
            "shuup.notify.actions:SetDebugFlag",
            "shuup.notify.actions:AddOrderLogEntry",
            "shuup.notify.actions:SendEmail",
            "shuup.notify.actions:AddNotification",
        ],
        "notify_event": [
            "shuup.notify.notify_events:PasswordReset",
        ],
        "notify_script_template": [
            "shuup.notify.script_templates:PasswordResetTemplate",
        ],
        "admin_module": [
            "shuup.notify.admin_module:NotifyAdminModule",
            "shuup.notify.admin_module:EmailTemplateAdminModule",
        ]
    }

    def ready(self):
        import shuup.notify.signal_handlers  # noqa F(401)


default_app_config = "shuup.notify.ShuupNotifyAppConfig"
