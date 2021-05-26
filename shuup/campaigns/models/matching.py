# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import hashlib
from django.db.models import Q

from shuup.campaigns.consts import CONTEXT_CONDITION_CACHE_NAMESPACE
from shuup.campaigns.models import CatalogFilter, CatalogFilterCachedShopProduct, CategoryFilter, ContextCondition
from shuup.core import cache
from shuup.core.models import ShopProduct
from shuup.core.utils import context_cache


def get_matching_context_conditions(context):
    namespace = CONTEXT_CONDITION_CACHE_NAMESPACE
    ctx_cache_elements = dict(customer=context.customer.pk or 0, shop=context.shop.pk)
    sorted_items = dict(sorted(ctx_cache_elements.items(), key=lambda item: item[0]))
    conditions_cache_key = "%s:%s" % (namespace, hashlib.sha1(str(sorted_items).encode("utf-8")).hexdigest())
    matching_context_conditions = cache.get(conditions_cache_key, None)
    if matching_context_conditions is None:
        matching_context_conditions = set()
        for condition in ContextCondition.objects.filter(active=True):
            if condition.matches(context):
                matching_context_conditions.add(condition.pk)
        cache.set(conditions_cache_key, matching_context_conditions, timeout=None)
    return matching_context_conditions


def update_matching_category_filters(shop_product, ids):
    filters = CategoryFilter.objects.filter(categories__id__in=ids)
    q = _get_filter_query(shop_product)
    all_shop_products = [shop_product] + list(ShopProduct.objects.filter(q))
    all_ids = [sp.pk for sp in all_shop_products]

    CatalogFilterCachedShopProduct.objects.filter(filter__in=filters, shop_product__id__in=all_ids).delete()

    for filter in filters:
        for sp in all_shop_products:
            if filter.matches(sp):
                CatalogFilterCachedShopProduct.objects.create(filter=filter, shop_product=sp)
                context_cache.bump_cache_for_shop_product(sp)  # is this necessary, smells like double


def update_matching_catalog_filters(shop_product_or_filter):
    if isinstance(shop_product_or_filter, CatalogFilter):
        CatalogFilterCachedShopProduct.objects.filter(filter=shop_product_or_filter).delete()
        for matching_product in shop_product_or_filter.get_matching_shop_products():
            CatalogFilterCachedShopProduct.objects.create(filter=shop_product_or_filter, shop_product=matching_product)
            context_cache.bump_cache_for_shop_product(matching_product)
        return

    shop_product = shop_product_or_filter

    from shuup.campaigns.utils.matcher import get_matching_for_product

    q = _get_filter_query(shop_product)
    all_shop_products = [shop_product] + list(ShopProduct.objects.filter(q))
    all_ids = [sp.pk for sp in all_shop_products]

    ids = get_matching_for_product(
        shop_product_or_filter,
        provide_category="campaign_catalog_filter",
        skippable_classes=[CatalogFilter],  # these will be handled separately in update_matching_category_filters
    )
    CatalogFilterCachedShopProduct.objects.filter(filter__id__in=ids, shop_product__id__in=all_ids).delete()
    for filter in CatalogFilter.objects.filter(id__in=ids):
        for sp in all_shop_products:
            if filter.matches(sp):
                CatalogFilterCachedShopProduct.objects.create(filter=filter, shop_product=sp)
                context_cache.bump_cache_for_shop_product(sp)


def get_matching_catalog_filters(shop_product):
    return shop_product.cached_catalog_campaign_filters.values_list("filter__id", flat=True)


def _get_filter_query(shop_product):
    q = Q()
    q |= Q(product__variation_parent_id=shop_product.product)
    if shop_product.product.variation_parent:
        q |= Q(product_id=shop_product.product.variation_parent.id)
    return q
