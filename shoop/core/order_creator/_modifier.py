# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.transaction import atomic

from shoop.core.models import Order

from ._creator import OrderProcessor


class OrderModifier(OrderProcessor):

    @atomic
    def update_order_from_source(self, order_source, order):
        data = self.get_source_base_data(order_source)
        Order.objects.filter(pk=order.pk).update(**data)

        order = Order.objects.get(pk=order.pk)

        for line in order.lines.all():
            line.delete()

        return self.finalize_creation(order, order_source)
