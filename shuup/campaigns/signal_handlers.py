# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.campaigns.consts import (
    CAMPAIGNS_CACHE_NAMESPACE, CATALOG_FILTER_CACHE_NAMESPACE,
    CONTEXT_CONDITION_CACHE_NAMESPACE
)
from shuup.campaigns.models import CatalogFilter
from shuup.campaigns.models.contact_group_sales_ranges import \
    ContactGroupSalesRange
from shuup.campaigns.models.matching import update_matching_catalog_filters
from shuup.campaigns.utils.matcher import get_matching_for_product
from shuup.core import cache
from shuup.core.models import Category, ShopProduct

from .utils.sales_range import assign_to_group_based_on_sales


def update_customers_groups(sender, instance, **kwargs):
    if not instance.order.customer:
        return
    assign_to_group_based_on_sales(ContactGroupSalesRange, instance.order.shop, instance.order.customer)


def invalidate_context_condition_cache(sender, instance, **kwargs):
    cache.bump_version(CAMPAIGNS_CACHE_NAMESPACE)
    cache.bump_version(CONTEXT_CONDITION_CACHE_NAMESPACE)


def update_filter_cache(sender, instance, **kwargs):
    invalidate_context_filter_cache(sender, instance=instance, **kwargs)
    if isinstance(instance, CatalogFilter):
        update_matching_catalog_filters(instance)
    elif isinstance(instance, ShopProduct):
        for filter_id in get_matching_for_product(instance, provide_category="campaign_catalog_filter"):
            filter = CatalogFilter.objects.get(pk=filter_id)
            update_matching_catalog_filters(filter)
    elif isinstance(instance, Category):
        for shop_product in instance.shop_products.all():
            for filter_id in get_matching_for_product(shop_product, provide_category="campaign_catalog_filter"):
                filter = CatalogFilter.objects.get(pk=filter_id)
                update_matching_catalog_filters(filter)


def invalidate_context_filter_cache(sender, instance, **kwargs):
    cache.bump_version(CAMPAIGNS_CACHE_NAMESPACE)
    # Let's try to preserve catalog filter cache as long as possible
    cache.bump_version("%s:%s" % (CATALOG_FILTER_CACHE_NAMESPACE, instance.pk))
