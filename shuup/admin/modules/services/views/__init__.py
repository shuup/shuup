# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from ._delete import PaymentMethodDeleteView, ShippingMethodDeleteView
from ._edit import PaymentMethodEditView, ShippingMethodEditView
from ._list import PaymentMethodListView, ShippingMethodListView

__all__ = [
    "PaymentMethodDeleteView",
    "PaymentMethodEditView",
    "PaymentMethodListView",
    "ShippingMethodDeleteView",
    "ShippingMethodEditView",
    "ShippingMethodListView"
]
