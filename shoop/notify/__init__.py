# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import shoop.apps

from .base import Condition, Action, Event, Variable, Binding
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


class AppConfig(shoop.apps.AppConfig):
    name = __name__
    verbose_name = "Shoop Notification Framework"
    label = "shoop_notify"
    provides = {
        "notify_condition": [
            __name__ + ".conditions:LanguageEqual",
            __name__ + ".conditions:BooleanEqual",
            __name__ + ".conditions:IntegerEqual",
            __name__ + ".conditions:TextEqual",
            __name__ + ".conditions:Empty",
            __name__ + ".conditions:NonEmpty",
        ],
        "notify_action": [
            __name__ + ".actions:SetDebugFlag",
            __name__ + ".actions:AddOrderLogEntry",
            __name__ + ".actions:SendEmail",
            __name__ + ".actions:AddNotification",
        ],
        "notify_event": [],
        "admin_module": [
            __name__ + ".admin_module:NotifyAdminModule",
        ]
    }


default_app_config = __name__ + ".AppConfig"
