# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from .edit import PaymentMethodEditView, ShippingMethodEditView
from .edit_detail import (
    PaymentMethodEditDetailView, ShippingMethodEditDetailView
)
from .list import PaymentMethodListView, ShippingMethodListView

__all__ = [
    "ShippingMethodEditView",
    "ShippingMethodEditDetailView",
    "ShippingMethodListView",
    "PaymentMethodEditView",
    "PaymentMethodEditDetailView",
    "PaymentMethodListView",
]
