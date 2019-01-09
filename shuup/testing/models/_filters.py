# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import models

from shuup.campaigns.models import CatalogFilter
from shuup.core.models import (
    Category, Contact, Product, ProductType, ShopProduct
)


class UltraFilter(CatalogFilter):
    model = Category
    identifier = "ufilter2"
    name = "ufilter2"
    products = models.ManyToManyField(Product, related_name='ultrafilter1')
    categories = models.ManyToManyField(Category, related_name='ultrafilter2')
    product_types = models.ManyToManyField(ProductType, related_name='ultrafilter3')
    shop_products = models.ManyToManyField(ShopProduct, related_name='ultrafilter4')

    product = models.ForeignKey(Product, null=True)
    category = models.ForeignKey(Category, null=True, related_name='ultrafilte5')
    product_type = models.ForeignKey(ProductType, null=True)
    derp = models.ForeignKey(Category, null=True, related_name='ultrafilte55')
    contact = models.ForeignKey(Contact, null=True)
    shop_product = models.ForeignKey(ShopProduct, null=True)
