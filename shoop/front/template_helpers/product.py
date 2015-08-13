# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from jinja2.utils import contextfunction

from shoop.core.models import AttributeVisibility, Product, ProductAttribute, ProductCrossSell, ProductCrossSellType


def get_visible_attributes(product):
    return ProductAttribute.objects.filter(
        product=product,
        attribute__visibility_mode=AttributeVisibility.SHOW_ON_PRODUCT_PAGE
    )


# Deprecated, see `get_product_cross_sells()`
@contextfunction
def get_products_bought_with(context, product, count=5):
    related_product_cross_sells = (
        ProductCrossSell.objects
        .filter(product1=product, type=ProductCrossSellType.COMPUTED)
        .order_by("-weight")[:(count * 4)])
    products = []
    for cross_sell in related_product_cross_sells:
        product2 = cross_sell.product2
        if product2.is_visible_to_user(context["request"].user) and product2.is_list_visible():
            products.append(product2)
        if len(products) >= count:
            break
    return products


@contextfunction
def is_visible(context, product):
    request = context["request"]
    shop_product = product.get_shop_instance(shop=request.shop)
    for error in shop_product.get_visibility_errors(customer=request.customer):  # pragma: no branch
        return False
    return True


@contextfunction
def get_product_cross_sells(context, product, relation_type="related", count=4):
    request = context["request"]
    rtype = ProductCrossSellType.RELATED
    if relation_type == "computed":
        rtype = ProductCrossSellType.COMPUTED
    elif relation_type == "recommended":
        rtype = ProductCrossSellType.RECOMMENDED

    related_product_ids = set((
        ProductCrossSell.objects
        .filter(product1=product, type=rtype)
        .order_by("-weight")[:(count * 4)]).values_list("product2_id", flat=True)
    )

    # TODO: Return in weight order
    related_products = Product.objects.filter(
        id__in=related_product_ids
    ).list_visible(shop=request.shop, customer=request.customer)

    return related_products[:count]
