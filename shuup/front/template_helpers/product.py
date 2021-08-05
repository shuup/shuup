# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.models.functions import Coalesce
from jinja2.utils import contextfunction
from typing import Iterable

from shuup.core.catalog import ProductCatalog, ProductCatalogContext
from shuup.core.models import (
    AttributeVisibility,
    Product,
    ProductAttribute,
    ProductCrossSell,
    ProductCrossSellType,
    ShopProductVisibility,
    get_person_contact,
)
from shuup.core.utils.product_subscription import ProductSubscriptionContext, get_product_subscription_options
from shuup.utils.text import force_ascii


def get_visible_attributes(product):
    return ProductAttribute.objects.filter(
        product=product, attribute__visibility_mode=AttributeVisibility.SHOW_ON_PRODUCT_PAGE
    )


def get_subscription_options_for_product(shop, product, supplier=None, user=None, **kwargs):
    context = ProductSubscriptionContext(shop, product, supplier, user)
    return list(get_product_subscription_options(context, **kwargs))


def _get_cross_sell_products(
    context,
    product: Product,
    types: Iterable[ProductCrossSellType],
    count=5,
    orderable_only=True,
    use_variation_parents=False,
):
    related_product_cross_sells = ProductCrossSell.objects.filter(type__in=types)
    # if this product is parent, then use all children instead
    if product.is_variation_parent():
        # Remember to exclude relations with the same parent
        related_product_cross_sells = related_product_cross_sells.filter(
            product1__in=product.variation_children.all()
        ).exclude(product2__in=product.variation_children.all())
    else:
        related_product_cross_sells = ProductCrossSell.objects.filter(product1=product)

    if use_variation_parents:
        related_product_cross_sells = set(
            related_product_cross_sells.order_by("-weight")
            .values_list(Coalesce("product2__variation_parent_id", "product2_id"), "weight")
            .distinct()
        )
    else:
        related_product_cross_sells = set(
            related_product_cross_sells.order_by("-weight").values_list("product2_id", "weight").distinct()
        )

    products_ids = [pcs[0] for pcs in related_product_cross_sells]

    request = context["request"]
    customer = get_person_contact(request.user)
    catalog = ProductCatalog(
        ProductCatalogContext(
            shop=request.shop,
            user=getattr(request, "user", None),
            contact=customer,
            purchasable_only=orderable_only,
            visibility=ShopProductVisibility.LISTED,
        )
    )
    products = catalog.get_products_queryset().filter(pk__in=products_ids).distinct()[:count]
    return sorted(products, key=lambda product: products_ids.index(product.id))


@contextfunction
def get_products_bought_with(context, product: Product, count=5, orderable_only=True, use_variation_parents=True):
    types = [ProductCrossSellType.BOUGHT_WITH, ProductCrossSellType.COMPUTED]
    return _get_cross_sell_products(context, product, types, count, orderable_only, use_variation_parents)


@contextfunction
def is_visible(context, product):
    request = context["request"]
    shop_product = product.get_shop_instance(shop=request.shop, allow_cache=True)
    return shop_product.is_visible(request.customer)


@contextfunction
def get_product_cross_sells(
    context,
    product,
    relation_type=ProductCrossSellType.RELATED,
    count=4,
    orderable_only=True,
    use_variation_parents=False,
):
    rtype = map_relation_type(relation_type)
    return _get_cross_sell_products(
        context,
        product,
        types=[rtype],
        count=count,
        orderable_only=orderable_only,
        use_variation_parents=use_variation_parents,
    )


def map_relation_type(relation_type):
    """
    Map relation type to enum value.

    :type relation_type: ProductCrossSellType|str
    :rtype: ProductCrossSellType
    :raises: `LookupError` if unknown string is given
    """
    if isinstance(relation_type, ProductCrossSellType):
        return relation_type
    attr_name = force_ascii(relation_type).upper()
    try:
        return getattr(ProductCrossSellType, attr_name)
    except AttributeError:
        raise LookupError("Unknown ProductCrossSellType %r" % (relation_type,))
