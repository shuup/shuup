# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from .delete import ProductDeleteView
from .edit import ProductEditView
from .edit_cross_sell import ProductCrossSellEditView
from .edit_media import ProductMediaEditView
from .list import ProductListView
from .variation import ProductVariationView

__all__ = [
    "ProductCrossSellEditView",
    "ProductDeleteView",
    "ProductEditView",
    "ProductListView",
    "ProductVariationView",
    "ProductMediaEditView",
]
