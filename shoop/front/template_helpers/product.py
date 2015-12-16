# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.deprecation import warn_about_renamed_method
from jinja2.utils import contextfunction

from shoop.core import cache
from shoop.core.models import AttributeVisibility, Product, ProductAttribute, ProductCrossSell, ProductCrossSellType
from shoop.utils.enums import map_enum
from shoop.utils.models import get_in_id_order


def get_visible_attributes(product):
    return ProductAttribute.objects.filter(
        product=product,
        attribute__visibility_mode=AttributeVisibility.SHOW_ON_PRODUCT_PAGE
    )


# Deprecated, see `get_related_products()`
@contextfunction
@warn_about_renamed_method("", "get_products_bought_with", "get_related_products", DeprecationWarning)
def get_products_bought_with(context, product, count=5):
    return get_related_products(context, product, "computed", count)


@contextfunction
def is_visible(context, product):
    request = context["request"]
    shop_product = product.get_shop_instance(shop=request.shop)
    for error in shop_product.get_visibility_errors(customer=request.customer):  # pragma: no branch
        return False
    return True


@contextfunction
@warn_about_renamed_method("", "get_product_cross_sells", "get_related_products", DeprecationWarning)
def get_product_cross_sells(context, product, relation_type="related", count=4):
    return get_related_products(context, product, relation_type, count)


@contextfunction
def get_related_products(context, product, relation_type="related", count=4):
    """
    Get at most `count` visible products related (by type `relation_type`) to the given `product`.

    :param context: The rendering context. This parameter is passed implicitly by Jinja2.
    :type context: jinja2.runtime.Context
    :param product: Source product
    :type product: shoop.core.models.Product
    :param relation_type: Relation type (string or ProductCrossSellType value)
    :type relation_type: str|ProductCrossSellType
    :param count: Number of products to return.
    :type count: int
    :return: List of at most `count` products.
    :rtype: list[shoop.core.models.Product]
    :raises ValueError: ValueError may be raised if the `relation_type` passed isn't valid.
    """
    relation_type = map_enum(ProductCrossSellType, relation_type)
    id_query_count = max(count * 4, 64)  # IDs to query for caching
    cache_key = "related_product_ids:%d_%d_%d" % (product.pk, relation_type.value, id_query_count)
    related_product_ids = cache.get(cache_key)
    if related_product_ids is None:
        related_product_ids = list(
            ProductCrossSell.objects
            .filter(product1=product, type=relation_type)
            .order_by("weight")[:id_query_count].values_list("product2_id", flat=True)
        )
        cache.set(cache_key, related_product_ids)

    if not related_product_ids:
        return []

    request = context["request"]

    return get_in_id_order(
        Product.objects.list_visible(shop=request.shop, customer=request.customer),
        related_product_ids,
        count
    )
