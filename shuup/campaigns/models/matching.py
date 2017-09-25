# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.models import Q

from shuup.campaigns.consts import CONTEXT_CONDITION_CACHE_NAMESPACE
from shuup.campaigns.models import ContextCondition
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


def get_matching_catalog_filters(shop_product):
    return shop_product.cached_catalog_campaign_filters.values_list('filter__id', flat=True)


def _get_filter_query(shop_product):
    q = Q()
    q |= Q(product__variation_parent_id=shop_product.product)
    if shop_product.product.variation_parent:
        q |= Q(product_id=shop_product.product.variation_parent.id)
    return q
