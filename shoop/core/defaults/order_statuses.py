# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.core.models import OrderStatus, OrderStatusRole


def create_default_order_statuses():
    for i, props in enumerate([
        {"name": u"received", "role": OrderStatusRole.INITIAL, "identifier": "recv", "default": True},
        {"name": u"in progress", "identifier": "prog"},
        {"name": u"complete", "role": OrderStatusRole.COMPLETE, "identifier": "comp", "default": True},
        {"name": u"canceled", "role": OrderStatusRole.CANCELED, "identifier": "canc", "default": True}
    ]):
        if not OrderStatus.objects.filter(identifier=props["identifier"]).exists():
            OrderStatus.objects.create(ordering=i, **props)
