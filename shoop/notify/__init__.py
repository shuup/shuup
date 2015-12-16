# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from shoop.apps import AppConfig

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


class ShoopNotifyAppConfig(AppConfig):
    name = "shoop.notify"
    verbose_name = "Shoop Notification Framework"
    label = "shoop_notify"
    provides = {
        "notify_condition": [
            "shoop.notify.conditions:LanguageEqual",
            "shoop.notify.conditions:BooleanEqual",
            "shoop.notify.conditions:IntegerEqual",
            "shoop.notify.conditions:TextEqual",
            "shoop.notify.conditions:Empty",
            "shoop.notify.conditions:NonEmpty",
        ],
        "notify_action": [
            "shoop.notify.actions:SetDebugFlag",
            "shoop.notify.actions:AddOrderLogEntry",
            "shoop.notify.actions:SendEmail",
            "shoop.notify.actions:AddNotification",
        ],
        "notify_event": [],
        "admin_module": [
            "shoop.notify.admin_module:NotifyAdminModule",
        ]
    }


default_app_config = "shoop.notify.ShoopNotifyAppConfig"
