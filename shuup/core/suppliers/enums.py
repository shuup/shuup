# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum


class StockAdjustmentType(Enum):
    INVENTORY = 1
    RESTOCK = 2
    RESTOCK_LOGICAL = 3

    class Labels:
        INVENTORY = _("inventory")
        RESTOCK = _("restock")
        RESTOCK_LOGICAL = _("restock logical")
