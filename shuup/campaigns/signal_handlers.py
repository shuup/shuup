# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.campaigns.consts import (
    CAMPAIGNS_CACHE_NAMESPACE,
    CATALOG_FILTER_CACHE_NAMESPACE,
    CONTEXT_CONDITION_CACHE_NAMESPACE,
)
from shuup.campaigns.models import CatalogFilter
from shuup.campaigns.models.contact_group_sales_ranges import ContactGroupSalesRange
from shuup.campaigns.models.matching import update_matching_catalog_filters, update_matching_category_filters
from shuup.core import cache
from shuup.core.models import Category, ShopProduct

from .exceptions import CampaignsInvalidInstanceForCacheUpdate
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
        # shop product being saved
        action = kwargs.get("action")
        if not action:
            # this is plain ``ShopProduct`` save
            update_matching_catalog_filters(instance)
        else:
            # This comes from categories through and it should only
            # update those categories the shop product attached into
            ids = None
            if action in ["post_add", "post_remove"]:
                ids = kwargs["pk_set"]
            if ids:
                if instance and instance.primary_category:
                    ids.add(instance.primary_category.pk)
                update_matching_category_filters(instance, ids)
    elif isinstance(instance, Category):
        for shop_product in instance.shop_products.all():
            update_matching_catalog_filters(shop_product)
    else:
        raise CampaignsInvalidInstanceForCacheUpdate("Invalid instance type.")


def invalidate_context_filter_cache(sender, instance, **kwargs):
    cache.bump_version(CAMPAIGNS_CACHE_NAMESPACE)
    # Let's try to preserve catalog filter cache as long as possible
    cache.bump_version("%s:%s" % (CATALOG_FILTER_CACHE_NAMESPACE, instance.pk))
