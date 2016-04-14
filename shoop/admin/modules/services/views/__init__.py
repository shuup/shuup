# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from .edit import PaymentMethodEditView, ShippingMethodEditView
from .list import PaymentMethodListView, ShippingMethodListView

__all__ = [
    "PaymentMethodEditView",
    "PaymentMethodListView",
    "ShippingMethodEditView",
    "ShippingMethodListView"
]
