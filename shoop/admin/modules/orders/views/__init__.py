# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from .create import OrderCreateView
from .detail import OrderDetailView, OrderSetStatusView
from .list import OrderListView
from .shipment import OrderCreateShipmentView

__all__ = ["OrderDetailView", "OrderListView", "OrderCreateShipmentView", "OrderSetStatusView", "OrderCreateView"]
