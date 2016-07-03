# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from shuup.campaigns.consts import (
    CATALOG_FILTER_CACHE_NAMESPACE, CONTEXT_CONDITION_CACHE_NAMESPACE
)
from shuup.campaigns.models import CatalogFilter, ContextCondition
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
        for condition in ContextCondition.objects.all():
            if condition.matches(context):
                matching_context_conditions.add(condition.pk)
        cache.set(conditions_cache_key, matching_context_conditions, timeout=None)
    return matching_context_conditions


def get_matching_catalog_filters(shop_product):
    namespace = CATALOG_FILTER_CACHE_NAMESPACE
    catalog_filters_cache_key = "%s:%s" % (namespace, shop_product.pk)
    matching_catalog_filters = cache.get(catalog_filters_cache_key, None)
    if matching_catalog_filters is None:
        matching_catalog_filters = set()
        for filter in CatalogFilter.objects.all():
            if filter.matches(shop_product):
                matching_catalog_filters.add(filter.pk)
        cache.set(catalog_filters_cache_key, matching_catalog_filters, timeout=None)
    return matching_catalog_filters
