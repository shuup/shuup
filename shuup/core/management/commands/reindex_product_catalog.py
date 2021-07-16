# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.core.management.base import BaseCommand

from shuup.core.catalog import ProductCatalog
from shuup.core.models import ShopProduct


class Command(BaseCommand):
    help = "Reindex the prices and availability of all products of the catalog"

    def handle(self, *args, **options):
        for shop_product in ShopProduct.objects.all():
            ProductCatalog.index_shop_product(shop_product)
