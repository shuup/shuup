# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from shuup.apps import AppConfig

from .base import Action, Binding, Condition, Event, Variable
from .enums import ConstantUse, TemplateUse
from .script import Context

__all__ = (
    "Action",
    "Binding",
    "Context",
    "Condition",
    "ConstantUse",
    "Event",
    "TemplateUse",
    "Variable",
)


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
        "notify_event": [],
        "admin_module": [
            "shuup.notify.admin_module:NotifyAdminModule",
        ]
    }


default_app_config = "shuup.notify.ShuupNotifyAppConfig"
