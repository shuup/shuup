# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.models.signals import post_save
from django.dispatch import receiver

from shuup.core.models import Manufacturer, Shop, ShopProduct
from shuup.core.signals import context_cache_item_bumped  # noqa
from shuup.core.utils import context_cache
from shuup.front.utils import cache as cache_utils


@receiver(context_cache_item_bumped, dispatch_uid="context-cache-item-bumped")
def handle_context_cache_item_bumped(sender, item, **kwargs):
    """
    Every time the context cache is bumped for a ShopProduct
    we bump the context cache for template helpers for the item's shop
    """
    if isinstance(item, ShopProduct):
        shop = item.shop
        context_cache.bump_cache_for_item(cache_utils.get_best_selling_products_cache_item(shop))
        context_cache.bump_cache_for_item(cache_utils.get_newest_products_cache_item(shop))
        context_cache.bump_cache_for_item(cache_utils.get_products_for_category_cache_item(shop))
        context_cache.bump_cache_for_item(cache_utils.get_random_products_cache_item(shop))


def handle_manufacturer_post_save(sender, instance, **kwargs):
    """
    Everytime a manufacturer gets saved, we bump our caches for manufacturer's shop or all shops
    """
    if instance.shops.exists():
        for shop in instance.shops.only("pk").all():
            context_cache.bump_cache_for_item(cache_utils.get_all_manufacturers_cache_item(shop))
    else:
        # worst scenario ever
        for shop in Shop.objects.only("pk").all():
            context_cache.bump_cache_for_item(cache_utils.get_all_manufacturers_cache_item(shop))


post_save.connect(handle_manufacturer_post_save, sender=Manufacturer)
