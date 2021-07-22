# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.dispatch import receiver

from shuup.core.catalog.signals import index_catalog_shop_product
from shuup.core.tasks import run_task


@receiver(index_catalog_shop_product)
def on_index_catalog_shop_product(sender, shop_product, **kwargs):
    run_task("shuup.simple_supplier.tasks.index_shop_product", shop_product=shop_product.pk)