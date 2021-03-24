# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import warnings
from django.conf import settings
from jinja2.utils import contextfunction

from shuup.core.models import (
    AttributeVisibility,
    Product,
    ProductAttribute,
    ProductCrossSell,
    ProductCrossSellType,
    ProductMode,
    ShopProduct,
    Supplier,
    get_person_contact,
)
from shuup.core.utils import context_cache
from shuup.core.utils.product_subscription import ProductSubscriptionContext, get_product_subscription_options
from shuup.front.utils import cache as cache_utils
from shuup.utils.text import force_ascii


def get_visible_attributes(product):
    return ProductAttribute.objects.filter(
        product=product, attribute__visibility_mode=AttributeVisibility.SHOW_ON_PRODUCT_PAGE
    )


def get_subscription_options_for_product(shop, product, supplier=None, user=None, **kwargs):
    context = ProductSubscriptionContext(shop, product, supplier, user)
    return list(get_product_subscription_options(context, **kwargs))


# Deprecated, see `get_product_cross_sells()`
@contextfunction
def get_products_bought_with(context, product, count=5):
    warnings.warn("Warning! Products bought with template helper is deprecated.", DeprecationWarning)
    related_product_cross_sells = set(
        ProductCrossSell.objects.filter(product1=product, type=ProductCrossSellType.COMPUTED)
        .values_list("product2_id", flat=True)
        .order_by("-weight")[: (count * 4)]
    )

    request = context["request"]
    customer = get_person_contact(request.user)
    return Product.objects.listed(shop=request.shop, customer=customer).filter(pk__in=related_product_cross_sells)[
        :count
    ]


@contextfunction
def is_visible(context, product):
    request = context["request"]
    shop_product = product.get_shop_instance(shop=request.shop, allow_cache=True)
    return shop_product.is_visible(request.customer)


@contextfunction  # noqa (C901)
def get_product_cross_sells(
    context,
    product,
    relation_type=ProductCrossSellType.RELATED,
    count=4,
    orderable_only=True,
    use_variation_parents=False,
):
    request = context["request"]

    key, products = context_cache.get_cached_value(
        identifier="product_cross_sells",
        item=cache_utils.get_cross_sells_cache_item(request.shop),
        context=request,
        product=product,
        relation_type=relation_type,
        count=count,
        orderable_only=orderable_only,
        use_variation_parents=use_variation_parents,
    )

    if products is not None:
        return products

    rtype = map_relation_type(relation_type)

    # if this product is parent, then use all children instead
    if product.mode in [ProductMode.VARIABLE_VARIATION_PARENT, ProductMode.SIMPLE_VARIATION_PARENT]:
        # Remember to exclude relations with the same parent
        cross_sell_products = ProductCrossSell.objects.filter(
            product1__in=product.variation_children.visible(request.shop, customer=request.customer), type=rtype
        ).exclude(product2__in=product.variation_children.visible(request.shop, customer=request.customer))
    else:
        cross_sell_products = ProductCrossSell.objects.filter(product1=product, type=rtype)

    related_product_ids = list(
        cross_sell_products.order_by("weight")[: (count * 4)].values_list("product2_id", flat=True)
    )

    sorted_related_products = []
    for product in Product.objects.filter(id__in=related_product_ids):
        sort_order = related_product_ids.index(product.pk)

        # use the variation parent when configured
        if use_variation_parents and product.variation_parent:
            product = product.variation_parent

        try:
            shop_product = product.get_shop_instance(request.shop, allow_cache=True)
        except ShopProduct.DoesNotExist:
            continue
        if orderable_only:
            for supplier in Supplier.objects.enabled(shop=request.shop):
                if shop_product.is_orderable(
                    supplier, request.customer, shop_product.minimum_purchase_quantity, allow_cache=True
                ):
                    sorted_related_products.append((sort_order, product))
                    break
        elif shop_product.is_visible(request.customer):
            sorted_related_products.append((sort_order, product))

    # Order related products by weight. Related product ids is in weight order.
    # If same related product is linked twice to product then lowest weight stands.
    sorted_related_products.sort(key=lambda pair: pair[0])
    products = []

    for sort_order, product in sorted_related_products[:count]:
        if product not in products:
            products.append(product)

    context_cache.set_cached_value(key, products, settings.SHUUP_TEMPLATE_HELPERS_CACHE_DURATION)
    return products


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
