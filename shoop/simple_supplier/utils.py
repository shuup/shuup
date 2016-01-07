# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.models import Sum

from shoop.core.models import OrderLine, OrderStatusRole, ShipmentProduct

from .models import StockAdjustment


def get_current_stock_value(supplier_id, product_id):
    # TODO: Consider whether this should be done with an SQL view
    events = (
        StockAdjustment.objects
        .filter(supplier_id=supplier_id, product_id=product_id)
        .aggregate(total=Sum("delta"))["total"] or 0)
    orders_bought = (
        OrderLine.objects
        .filter(supplier_id=supplier_id, product_id=product_id)
        .exclude(order__status__role=OrderStatusRole.CANCELED)
        .aggregate(total=Sum("quantity"))["total"] or 0)
    orders_sent = (
        ShipmentProduct.objects
        .filter(shipment__supplier=supplier_id, product_id=product_id)
        .aggregate(total=Sum("quantity"))["total"] or 0)
    return {
        "logical_count": events - orders_bought,
        "physical_count": events - orders_sent
    }
