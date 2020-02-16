# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from .addresses import OrderAddressEditView
from .detail import OrderDetailView, OrderSetStatusView
from .edit import OrderEditView, UpdateAdminCommentView
from .list import OrderListView
from .log import NewLogEntryView
from .payment import (
    OrderCreatePaymentView, OrderDeletePaymentView, OrderSetPaidView
)
from .refund import OrderCreateFullRefundView, OrderCreateRefundView
from .shipment import OrderCreateShipmentView, ShipmentDeleteView
from .status import OrderStatusEditView, OrderStatusListView

__all__ = [
    "NewLogEntryView", "OrderAddressEditView", "OrderDetailView", "OrderEditView",
    "OrderListView", "OrderCreatePaymentView", "OrderCreateFullRefundView",
    "OrderCreateRefundView", "OrderCreateShipmentView", "OrderSetPaidView",
    "OrderSetStatusView", "OrderStatusEditView", "OrderStatusListView", "ShipmentDeleteView",
    "UpdateAdminCommentView", "OrderDeletePaymentView"
]
