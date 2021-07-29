# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import transaction
from django.dispatch import receiver

from shuup.admin.signals import object_saved
from shuup.core.catalog.signals import index_catalog_shop_product
from shuup.core.models import Product, ShopProduct
from shuup.core.tasks import run_task


@receiver(index_catalog_shop_product)
def on_index_catalog_shop_product(sender, shop_product, **kwargs):
    shop_product_id = shop_product.pk if isinstance(shop_product, ShopProduct) else shop_product
    run_task("shuup.simple_supplier.tasks.index_shop_product", shop_product=shop_product_id)


@receiver(object_saved)
def on_object_saved(sender, object, **kwargs):
    # update stocks after a shop product/product is saved
    if isinstance(object, ShopProduct):
        transaction.on_commit(
            lambda: run_task("shuup.simple_supplier.tasks.update_shop_product_stocks", shop_product=object.pk)
        )
    if isinstance(object, Product):
        transaction.on_commit(lambda: run_task("shuup.simple_supplier.tasks.update_product_stocks", product=object.pk))
