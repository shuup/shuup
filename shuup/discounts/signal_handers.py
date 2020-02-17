# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db.models.signals import m2m_changed, post_save, pre_delete

from shuup.core.models import Category, ShopProduct
from shuup.core.utils.price_cache import bump_all_price_caches
from shuup.discounts.exceptions import DiscountM2MChangeError
from shuup.discounts.models import (
    AvailabilityException, CouponCode, Discount, HappyHour, TimeRange
)
from shuup.discounts.utils import bump_price_expiration


def handle_discount_post_save(sender, instance, **kwargs):
    shops = set(instance.shops.values_list("pk", flat=True))
    bump_price_expiration(shops)
    bump_all_price_caches(shops)


def handle_happy_hour_post_save(sender, instance, **kwargs):
    # Bump caches only if discount object exists
    # This prevents to bump caches when an instance is created and it is not attached yey
    if instance.discounts.exists():
        shops = set(instance.discounts.values_list("shops__pk", flat=True))
        bump_price_expiration(shops)
        bump_all_price_caches(shops)


def handle_time_range_post_save(sender, instance, **kwargs):
    # Bump caches only if discount object exists
    # This prevents to bump caches when an instance is created and it is not attached yey
    if instance.happy_hour.discounts.exists():
        shops = set(instance.happy_hour.discounts.values_list("shops__pk", flat=True))
        bump_price_expiration(shops)
        bump_all_price_caches(shops)


def handle_availability_exception_post_save(sender, instance, **kwargs):
    # Bump caches only if discount object exists
    # This prevents to bump caches when an instance is created and it is not attached yey
    if instance.discounts.exists():
        shops = set(instance.discounts.values_list("shops__pk", flat=True))
        bump_price_expiration(shops)
        bump_all_price_caches(shops)


def handle_coupon_post_save(sender, instance, **kwargs):
    # Bump caches only if discount object exists
    # This prevents to bump caches when an instance is created and it is not attached yey
    if instance.coupon_code_discounts.exists():
        shops = set(instance.coupon_code_discounts.values_list("shops__pk", flat=True))
        bump_price_expiration(shops)
        bump_all_price_caches(shops)


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
    elif isinstance(instance, AvailabilityException):
        handle_availability_exception_post_save(sender, instance, **kwargs)
    else:
        raise DiscountM2MChangeError("Invalid instance type.")


# Bump price info and price expiration caches when Discount related models are changed
m2m_changed.connect(
    handle_generic_m2m_changed,
    sender=Discount.shops.through,
    dispatch_uid="discounts:changed_shops_m2m"
)
m2m_changed.connect(
    handle_generic_m2m_changed,
    sender=Discount.happy_hours.through,
    dispatch_uid="discounts:changed_happy_hours_m2m"
)
m2m_changed.connect(
    handle_generic_m2m_changed,
    sender=Discount.availability_exceptions.through,
    dispatch_uid="discounts:changed_availability_exceptions_m2m"
)

# Bump price info and price expiration caches when categories from shop products change
m2m_changed.connect(
    handle_generic_m2m_changed,
    sender=ShopProduct.categories.through,
    dispatch_uid="discounts:changed_shop_product_categories"
)

# Bump price info and price expiration caches when Discount instances are changed
post_save.connect(handle_discount_post_save, sender=Discount, dispatch_uid="discounts:change_discount")

# Bump price info and price expiration caches when HappyHour instances are changed or deleted
post_save.connect(handle_happy_hour_post_save, sender=HappyHour, dispatch_uid="discounts:change_happy_hour")
pre_delete.connect(handle_happy_hour_post_save, sender=HappyHour, dispatch_uid="discounts:delete_happy_hour")

# Bump price info and price expiration caches when TimeRange instances are changed or deleted
post_save.connect(handle_time_range_post_save, sender=TimeRange, dispatch_uid="discounts:change_time_range")
pre_delete.connect(handle_time_range_post_save, sender=TimeRange, dispatch_uid="discounts:delete_time_range")

# Bump price info and price expiration caches when CouponCode instances are changed or deleted
post_save.connect(handle_coupon_post_save, sender=CouponCode, dispatch_uid="discounts:change_coupon")
pre_delete.connect(handle_coupon_post_save, sender=CouponCode, dispatch_uid="discounts:delete_coupon")

# Bump price info and price expiration caches when AvailabilityException instances are changed
post_save.connect(
    handle_availability_exception_post_save,
    sender=AvailabilityException,
    dispatch_uid="discounts:availability_exception"
)
