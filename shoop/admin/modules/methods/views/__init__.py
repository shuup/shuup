# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from .edit import ShippingMethodEditView, PaymentMethodEditView
from .edit_detail import ShippingMethodEditDetailView, PaymentMethodEditDetailView
from .list import ShippingMethodListView, PaymentMethodListView

__all__ = [
    "ShippingMethodEditView",
    "ShippingMethodEditDetailView",
    "ShippingMethodListView",
    "PaymentMethodEditView",
    "PaymentMethodEditDetailView",
    "PaymentMethodListView",
]
