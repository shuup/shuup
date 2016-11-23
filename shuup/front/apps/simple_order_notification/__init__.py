# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.apps import AppConfig


class SimpleOrderNotificationAppConfig(AppConfig):
    name = "shuup.front.apps.simple_order_notification"
    verbose_name = "Shuup Frontend - Simple Order Notification"
    label = "shuup_front.simple_order_notification"

    provides = {
        "admin_module": [
            "shuup.front.apps.simple_order_notification.admin_module:SimpleOrderNotificationModule",
        ]
    }

    def ready(self):
        from shuup.front.signals import order_complete_viewed
        from shuup.front.apps.simple_order_notification.signal_handler import send_simple_order_notification
        order_complete_viewed.connect(
            send_simple_order_notification,
            dispatch_uid="simple_order_notification.send_simple_order_notification")


default_app_config = "shuup.front.apps.simple_order_notification.SimpleOrderNotificationAppConfig"
