# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import transaction
from django.db.models.signals import m2m_changed, post_save, pre_delete
from django.dispatch.dispatcher import receiver

from shuup.admin.signals import object_saved
from shuup.core.models import Category, ShopProduct
from shuup.core.tasks import run_task
from shuup.core.utils.price_cache import bump_all_price_caches
from shuup.discounts.exceptions import DiscountM2MChangeError
from shuup.discounts.models import Discount, HappyHour, TimeRange
from shuup.discounts.utils import bump_price_expiration


@receiver(object_saved, sender=Discount)
def on_discount_object_saved(sender, object: Discount, **kwargs):
    transaction.on_commit(lambda: run_task("shuup.discounts.tasks.reindex_discount", discount_id=object.pk))


@receiver(object_saved, sender=HappyHour)
def on_happy_hour_object_saved(sender, object: HappyHour, **kwargs):
    transaction.on_commit(lambda: run_task("shuup.discounts.tasks.reindex_happy_hour", happy_hour_id=object.pk))


def handle_discount_post_save(sender, instance, **kwargs):
    shop_ids = set([instance.shop.pk])
    bump_price_expiration(shop_ids)
    bump_all_price_caches(shop_ids)


def handle_happy_hour_post_save(sender, instance, **kwargs):
    # Bump caches only if discount object exists
    # This prevents to bump caches when an instance is created and it is not attached yey
    if instance.discounts.exists():
        shop_ids = set(instance.discounts.values_list("shop__pk", flat=True))
        bump_price_expiration(shop_ids)
        bump_all_price_caches(shop_ids)


def handle_time_range_post_save(sender, instance, **kwargs):
    # Bump caches only if discount object exists
    # This prevents to bump caches when an instance is created and it is not attached yey
    if instance.happy_hour.discounts.exists():
        shop_ids = set(instance.happy_hour.discounts.values_list("shop__pk", flat=True))
        bump_price_expiration(shop_ids)
        bump_all_price_caches(shop_ids)


def handle_generic_m2m_changed(sender, instance, **kwargs):
    """
    As `instance` can be an instance of the sender or of the class the ManyToManyField is related to,
    we need to check the type of the instance and forward to the correct handler
    """
    if isinstance(instance, ShopProduct):
        bump_price_expiration([instance.shop_id])
        bump_all_price_caches([instance.shop_id])
    elif isinstance(instance, Category):
        for shop_id in set(instance.shop_products.all().values_list("shop_id", flat=True)):
            bump_price_expiration([shop_id])
            bump_all_price_caches([shop_id])
    elif isinstance(instance, Discount):
        handle_discount_post_save(sender, instance, **kwargs)
    elif isinstance(instance, HappyHour):
        handle_happy_hour_post_save(sender, instance, **kwargs)
    else:
        raise DiscountM2MChangeError("Invalid instance type.")


# Bump price info and price expiration caches when Discount related models are changed
m2m_changed.connect(
    handle_generic_m2m_changed, sender=Discount.happy_hours.through, dispatch_uid="discounts:changed_happy_hours_m2m"
)

# Bump price info and price expiration caches when categories from shop products change
m2m_changed.connect(
    handle_generic_m2m_changed,
    sender=ShopProduct.categories.through,
    dispatch_uid="discounts:changed_shop_product_categories",
)

# Bump price info and price expiration caches when Discount instances are changed
post_save.connect(handle_discount_post_save, sender=Discount, dispatch_uid="discounts:change_discount")

# Bump price info and price expiration caches when HappyHour instances are changed or deleted
post_save.connect(handle_happy_hour_post_save, sender=HappyHour, dispatch_uid="discounts:change_happy_hour")
pre_delete.connect(handle_happy_hour_post_save, sender=HappyHour, dispatch_uid="discounts:delete_happy_hour")

# Bump price info and price expiration caches when TimeRange instances are changed or deleted
post_save.connect(handle_time_range_post_save, sender=TimeRange, dispatch_uid="discounts:change_time_range")
pre_delete.connect(handle_time_range_post_save, sender=TimeRange, dispatch_uid="discounts:delete_time_range")
