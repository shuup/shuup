# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.dispatch import receiver

from shoop.notify import Event, Variable
from shoop.notify.typology import Email, Language, Model, Phone

from .signals import order_creator_finished


class OrderReceived(Event):
    identifier = "order_received"

    order = Variable("Order", type=Model("shoop.Order"))
    customer_email = Variable("Customer Email", type=Email)
    customer_phone = Variable("Customer Phone", type=Phone)
    language = Variable("Language", type=Language)


@receiver(order_creator_finished)
def send_order_received_notification(order, **kwargs):
    OrderReceived(
        order=order,
        customer_email=order.email,
        customer_phone=order.phone,
        language=order.language
    ).run()
