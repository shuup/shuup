# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from .detail import OrderDetailView, OrderSetStatusView
from .edit import OrderEditView, UpdateAdminCommentView
from .list import OrderListView
from .log import NewLogEntryView
from .payment import OrderCreatePaymentView, OrderSetPaidView
from .refund import OrderCreateFullRefundView, OrderCreateRefundView
from .shipment import OrderCreateShipmentView, ShipmentDeleteView

__all__ = [
    "NewLogEntryView", "OrderDetailView", "OrderEditView", "OrderListView",
    "OrderCreatePaymentView", "OrderCreateFullRefundView", "OrderCreateRefundView",
    "OrderCreateShipmentView", "OrderSetPaidView", "OrderSetStatusView",
    "ShipmentDeleteView", "UpdateAdminCommentView"
]
