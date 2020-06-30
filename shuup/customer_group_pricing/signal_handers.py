# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db.models.signals import m2m_changed, post_save, pre_delete
from django.dispatch import receiver

from shuup.admin.signals import product_copied
from shuup.core.models import Contact, ContactGroup
from shuup.core.utils.price_cache import bump_all_price_caches
from shuup.customer_group_pricing.models import CgpDiscount, CgpPrice


def handle_cgp_discount_post_save(sender, instance, **kwargs):
    bump_all_price_caches([instance.shop_id])


def handle_cgp_price_post_save(sender, instance, **kwargs):
    bump_all_price_caches([instance.shop_id])


def handle_contact_group_m2m_changed(sender, instance, **kwargs):
    if isinstance(instance, Contact):
        bump_all_price_caches(set(instance.shops.values_list("pk", flat=True)))
    elif isinstance(instance, ContactGroup):
        if instance.shop_id:
            bump_all_price_caches([instance.shop_id])
        else:
            bump_all_price_caches()


@receiver(product_copied, dispatch_uid="customer_group_pricing_product_copied")
def handle_product_copy(sender, shop, copied, copy, **kwargs):
    for price in CgpPrice.objects.filter(product=copied, shop=shop):
        CgpPrice.objects.create(
            product=copy, shop=shop, group=price.group,
            price_value=price.price_value
        )


# Bump prices cache when CgpDiscount is changed or deleted
post_save.connect(handle_cgp_discount_post_save, sender=CgpDiscount, dispatch_uid="cgp:change_cgp_discount")
pre_delete.connect(handle_cgp_discount_post_save, sender=CgpDiscount, dispatch_uid="cgp:delete_cgp_discount")

# Bump prices cache when CgpPrice is changed or deleted
post_save.connect(handle_cgp_price_post_save, sender=CgpPrice, dispatch_uid="cgp:change_cgp_price")
pre_delete.connect(handle_cgp_price_post_save, sender=CgpPrice, dispatch_uid="cgp:delete_cgp_price")

# Bump prices cache when ContactGroup members is changed
m2m_changed.connect(
    handle_contact_group_m2m_changed,
    sender=ContactGroup.members.through,
    dispatch_uid="cgp:change_contact_group_members"
)
