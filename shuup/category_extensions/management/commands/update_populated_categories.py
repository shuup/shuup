# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.management import BaseCommand

from shuup.category_extensions.models.category_populator import \
    CategoryPopulator
from shuup.core.models import ShopProduct


class Command(BaseCommand):

    def handle(self, *args, **options):
        for shop_product in ShopProduct.objects.all():
            for populator in CategoryPopulator.objects.all():
                if populator.category in shop_product.categories.all():
                    shop_product.categories.remove(populator.category)

                if populator.matches_product(shop_product):
                    shop_product.categories.add(populator.category)
