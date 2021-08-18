# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.core.catalog import ProductCatalog
from shuup.core.models import ProductMode, ShopProduct


def reindex_all_shop_products():
    for shop_product in ShopProduct.objects.exclude(product__mode=ProductMode.VARIATION_CHILD):
        ProductCatalog.index_shop_product(shop_product)
