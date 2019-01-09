# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings

from shuup.core.models import Category


def update_categories_post_save(sender, instance, **kwargs):
    if not getattr(settings, "SHUUP_AUTO_SHOP_PRODUCT_CATEGORIES", False):
        return

    if not instance.pk or not instance.primary_category:
        return

    categories = instance.categories.values_list("pk", flat=True)
    if instance.primary_category.pk not in categories:
        instance.categories.add(instance.primary_category)


def update_categories_through(sender, instance, **kwargs):
    action = kwargs.get("action", "post_add")
    if action != "post_add":
        return

    if not getattr(settings, "SHUUP_AUTO_SHOP_PRODUCT_CATEGORIES", False):
        return

    if not instance.pk:
        return
    if isinstance(instance, Category):
        shop_products = instance.shop_products.all()
        for shop_product in shop_products:
            set_shop_product_category(shop_product)
    else:
        set_shop_product_category(instance)


def set_shop_product_category(instance):
    if not instance.categories.count():
        return

    if not instance.primary_category:
        instance.primary_category = instance.categories.first()
        instance.save()
