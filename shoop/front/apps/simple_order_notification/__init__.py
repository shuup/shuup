# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import logging

from django.core.mail.message import EmailMessage
from django.template import engines
from django.template.utils import InvalidTemplateEngineError
from django.utils import translation

from shoop.apps import AppConfig
from shoop.utils.analog import LogEntryKind

from .templates import MESSAGE_BODY_TEMPLATE, MESSAGE_SUBJECT_TEMPLATE

LOG = logging.getLogger("shoop.simple_order_notification")
NOTIFICATION_SUCCESS_LOG_IDENTIFIER = "simple_order_notification_ok"
NOTIFICATION_ERROR_LOG_IDENTIFIER = "simple_order_notification_error"


def send_simple_order_notification(sender, order, request, **kwargs):
    """
    :param order: Order
    :type order: shoop.core.models.Order
    """

    if order.log_entries.filter(identifier=NOTIFICATION_SUCCESS_LOG_IDENTIFIER).exists():
        return

    try:
        engine = engines["jinja2"]
    except InvalidTemplateEngineError:
        return  # Dont send notifications because we cannot parse files :(

    with translation.override(order.language):
        # Local import to make sure the environment is initialized
        env = {"order": order}
        subject = engine.from_string(MESSAGE_SUBJECT_TEMPLATE).render(env)
        body = engine.from_string(MESSAGE_BODY_TEMPLATE).render(env)

    message = EmailMessage(subject, body, to=[order.email])
    try:
        message.send()
    except Exception as exc:
        LOG.exception("Failed to send order notification to %s" % message.to)
        order.add_log_entry(
            "Order Notification Email failed: %s" % exc,
            identifier=NOTIFICATION_ERROR_LOG_IDENTIFIER,
            kind=LogEntryKind.ERROR)
    else:
        LOG.info("Order notification sent to %s" % message.to)
        order.add_log_entry(
            "Order Notification Email sent",
            identifier=NOTIFICATION_SUCCESS_LOG_IDENTIFIER,
            kind=LogEntryKind.ERROR)


class SimpleOrderNotificationAppConfig(AppConfig):
    name = "shoop.front.apps.simple_order_notification"
    verbose_name = "Shoop Frontend - Simple Order Notification"
    label = "shoop_front.simple_order_notification"

    provides = {
        "admin_module": [
            "shoop.front.apps.simple_order_notification.admin_module:SimpleOrderNotificationModule",
        ]
    }

    def ready(self):
        from shoop.front.signals import order_complete_viewed

        order_complete_viewed.connect(
            send_simple_order_notification,
            dispatch_uid="simple_order_notification.send_simple_order_notification")


default_app_config = "shoop.front.apps.simple_order_notification.SimpleOrderNotificationAppConfig"
