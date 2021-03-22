# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from .delete import ProductDeleteView
from .edit import ProductEditView
from .edit_cross_sell import ProductCrossSellEditView
from .edit_media import ProductMediaBulkAdderView, ProductMediaEditView
from .edit_package import ProductPackageView
from .list import ProductListView
from .mass_edit import ProductMassEditView

__all__ = [
    "ProductCrossSellEditView",
    "ProductDeleteView",
    "ProductEditView",
    "ProductListView",
    "ProductPackageView",
    "ProductMediaEditView",
    "ProductMassEditView",
    "ProductMediaBulkAdderView",
]
