# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.core.management.base import BaseCommand
from django.db.transaction import atomic

from shuup.core.models import (
    OrderLine, OrderLineType, ProductCrossSell, ProductCrossSellType
)
from shuup.core.utils.product_bought_with_relations import \
    add_bought_with_relations_for_product


class Command(BaseCommand):

    @atomic
    def handle(self, *args, **options):
        # Clear all existing ProductCrossSell objects
        ProductCrossSell.objects.filter(type=ProductCrossSellType.BOUGHT_WITH).delete()

        # Handle all ordered products
        ordered_product_ids = OrderLine.objects.filter(type=OrderLineType.PRODUCT).values_list("product_id", flat=True)
        seen_product_ids = set()
        for product_id in ordered_product_ids:
            if product_id in seen_product_ids:
                continue
            seen_product_ids.add(product_id)
            add_bought_with_relations_for_product(product_id)
