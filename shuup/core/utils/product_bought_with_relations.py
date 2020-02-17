# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.db.models import Sum

from shuup.core.models import (
    OrderLine, OrderLineType, ProductCrossSell, ProductCrossSellType
)


def add_bought_with_relations_for_product(product_id, max_quantity=10):
    """
    Add ``ProductCrossSell`` objects with type
    ``ProductCrossSellType.BOUGHT_WITH`` based on other products
    ordered with product_id. Ordered amount is used as relation
    weight.

    :param product_id:  product_id to add relations to
    :type product_id: int
    :param max_quantity: maximum amount of relations created
    :type max_quantity: int
    """
    order_ids_to_check = OrderLine.objects.filter(
        product_id=product_id
    ).values_list(
        "order_id", flat=True
    )

    # Group all order lines related to given product_id
    # with product_id and calculate Sum of purchased quantities
    related_product_ids_and_quantities = OrderLine.objects.exclude(
        product_id=product_id
    ).filter(
        type=OrderLineType.PRODUCT,
        order_id__in=set(order_ids_to_check)
    ).values(
        "product_id"
    ).annotate(
        total_quantity=Sum("quantity")
    ).order_by(
        "-total_quantity"
    )[:max_quantity]

    # Add the actual cross-sells products
    for product_data in related_product_ids_and_quantities:
        ProductCrossSell.objects.create(
            product1_id=product_id,
            product2_id=product_data["product_id"],
            weight=product_data["total_quantity"],
            type=ProductCrossSellType.BOUGHT_WITH
        )
