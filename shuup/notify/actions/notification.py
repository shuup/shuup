# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import logging

from django.conf import settings

from shuup.notify.base import Action, Binding, ConstantUse, TemplatedBinding
from shuup.notify.enums import Priority, RecipientType
from shuup.notify.models import Notification
from shuup.notify.typology import Enum, Model, Text, URL


class AddNotification(Action):
    identifier = "add_notification"
    recipient_type = Binding(
        "Recipient Type",
        type=Enum(RecipientType),
        constant_use=ConstantUse.CONSTANT_ONLY,
        default=RecipientType.ADMINS
    )
    recipient = Binding(
        "Recipient",
        type=Model(settings.AUTH_USER_MODEL),
        constant_use=ConstantUse.VARIABLE_OR_CONSTANT,
        required=False
    )
    priority = Binding("Priority", type=Enum(Priority), constant_use=ConstantUse.CONSTANT_ONLY, default=Priority.NORMAL)
    message = TemplatedBinding("Message", type=Text, constant_use=ConstantUse.CONSTANT_ONLY, required=True)
    message_identifier = Binding("Message Identifier", Text, constant_use=ConstantUse.CONSTANT_ONLY, required=False)
    url = Binding("URL", type=URL, constant_use=ConstantUse.VARIABLE_OR_CONSTANT)

    def execute(self, context):
        """
        :type context: shuup.notify.script.Context
        """
        values = self.get_values(context)
        if values["recipient_type"] == RecipientType.SPECIFIC_USER:
            if not values["recipient"]:
                context.log(logging.WARN, "Warning! Misconfigured AddNotification -- no recipient for specific user.")
                return
        Notification.objects.create(
            recipient_type=values["recipient_type"],
            recipient=values["recipient"],
            priority=values["priority"],
            identifier=values.get("message_identifier"),
            message=values["message"][:140],
            url=values["url"],
            shop=context.shop
        )
