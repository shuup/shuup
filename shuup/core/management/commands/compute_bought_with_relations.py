# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.core.management.base import BaseCommand
from django.db.transaction import atomic

from shuup.core.models import (
    OrderLine, OrderLineType, ProductCrossSell, ProductCrossSellType, Shop
)
from shuup.core.utils import context_cache
from shuup.core.utils.product_bought_with_relations import (
    add_bought_with_relations_for_product
)
from shuup.front.utils import cache as cache_utils


class Command(BaseCommand):

    @atomic
    def handle(self, *args, **options):
        # Clear all existing ProductCrossSell objects
        ProductCrossSell.objects.filter(type=ProductCrossSellType.BOUGHT_WITH).delete()

        # Handle all ordered products
        ordered_product_ids = OrderLine.objects.filter(
            type=OrderLineType.PRODUCT).values_list("product_id", flat=True).distinct()
        for product_id in ordered_product_ids.distinct():
            add_bought_with_relations_for_product(product_id)

        for shop in Shop.objects.all():
            context_cache.bump_cache_for_item(cache_utils.get_cross_sells_cache_item(shop))
