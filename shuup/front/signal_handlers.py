# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.models.signals import post_save
from django.dispatch import receiver
from filer.models import Image

from shuup.core import cache
from shuup.core.models import (
    Manufacturer, ProductCrossSell, ProductMedia, Shop, ShopProduct
)
from shuup.core.signals import context_cache_item_bumped  # noqa
from shuup.core.utils import context_cache
from shuup.front.utils import cache as cache_utils
from shuup.front.utils.sorts_and_filters import bump_product_queryset_cache


@receiver(context_cache_item_bumped, dispatch_uid="context-cache-item-bumped")
def handle_context_cache_item_bumped(sender, **kwargs):

    def bump_cache_for_shop_id(shop_id):
        context_cache.bump_cache_for_item(cache_utils.get_listed_products_cache_item(shop_id))
        context_cache.bump_cache_for_item(cache_utils.get_best_selling_products_cache_item(shop_id))
        context_cache.bump_cache_for_item(cache_utils.get_newest_products_cache_item(shop_id))
        context_cache.bump_cache_for_item(cache_utils.get_products_for_category_cache_item(shop_id))
        context_cache.bump_cache_for_item(cache_utils.get_random_products_cache_item(shop_id))

    shop_id = kwargs.get("shop_id", None)
    if not shop_id:
        for shop_id in Shop.objects.values_list("id", flat=True):
            bump_cache_for_shop_id(shop_id)
    else:
        bump_cache_for_shop_id(shop_id)
    bump_product_queryset_cache()


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


def bump_instance_thumbnail_cache(sender, instance, **kwargs):
    cache_namespace = "thumbnail_{}_{}".format(instance.pk, instance.__class__.__name__)
    cache.bump_version(cache_namespace)


def handle_cross_sell_post_save(sender, instance, **kwargs):
    shop_ids = list(
        ShopProduct.objects.filter(
            product__in=[instance.product1, instance.product2]
        ).values_list("shop", flat=True).distinct()
    )
    for shop_id in shop_ids:
        context_cache.bump_cache_for_item(cache_utils.get_cross_sells_cache_item(shop_id))


post_save.connect(bump_instance_thumbnail_cache, sender=ProductMedia)
post_save.connect(bump_instance_thumbnail_cache, sender=Image)
post_save.connect(handle_manufacturer_post_save, sender=Manufacturer)
post_save.connect(handle_cross_sell_post_save, sender=ProductCrossSell)
