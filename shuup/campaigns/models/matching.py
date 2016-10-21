# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from shuup.campaigns.consts import CONTEXT_CONDITION_CACHE_NAMESPACE
from shuup.campaigns.models import (
    CatalogFilterCachedShopProduct, ContextCondition
)
from shuup.core import cache


def get_matching_context_conditions(context):
    namespace = CONTEXT_CONDITION_CACHE_NAMESPACE
    ctx_cache_elements = dict(
        customer=context.customer.pk or 0,
        shop=context.shop.pk)
    conditions_cache_key = "%s:%s" % (namespace, hash(frozenset(ctx_cache_elements.items())))
    matching_context_conditions = cache.get(conditions_cache_key, None)
    if matching_context_conditions is None:
        matching_context_conditions = set()
        for condition in ContextCondition.objects.filter(active=True):
            if condition.matches(context):
                matching_context_conditions.add(condition.pk)
        cache.set(conditions_cache_key, matching_context_conditions, timeout=None)
    return matching_context_conditions


def update_matching_catalog_filters(filter):
    # first, invalidate existing cache
    CatalogFilterCachedShopProduct.objects.filter(filter=filter).delete()

    # then add new items in
    for matching_product in filter.get_matching_shop_products():
        CatalogFilterCachedShopProduct.objects.create(filter=filter, shop_product=matching_product)


def get_matching_catalog_filters(shop_product):
    return shop_product.cached_catalog_campaign_filters.values_list('filter__id', flat=True)
