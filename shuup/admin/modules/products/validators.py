# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.admin.modules.products.issues import ProductValidationIssue
from shuup.core.models import (
    Shop,
    ShopProduct,
    Supplier,
)
from typing import Iterable


class AdminProductValidator:
    '''Base class for validating products.'''

    def get_validation_issues(shop_product: ShopProduct, shop: Shop, user,
            supplier: Supplier = None) -> Iterable[ProductValidationIssue]:
        pass
