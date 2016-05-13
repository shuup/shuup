# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from .detail import OrderDetailView, OrderSetStatusView
from .edit import OrderEditView
from .list import OrderListView
from .payment import OrderCreatePaymentView
from .shipment import OrderCreateShipmentView

__all__ = [
    "OrderDetailView", "OrderEditView", "OrderListView", "OrderCreatePaymentView",
    "OrderCreateShipmentView", "OrderSetStatusView"
]
