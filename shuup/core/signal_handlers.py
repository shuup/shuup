# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.backends.signals import connection_created
from django.db.models.signals import m2m_changed, post_migrate, post_save
from django.dispatch import receiver

from shuup.core.models import (
    Category,
    CompanyContact,
    ContactGroup,
    ContactGroupPriceDisplay,
    DisplayUnit,
    PersonContact,
    Product,
    Shop,
    ShopProduct,
    Supplier,
    Tax,
    TaxClass,
)
from shuup.core.models._contacts import get_groups_ids, get_price_display_options
from shuup.core.models._units import get_display_unit
from shuup.core.order_creator.signals import order_creator_finished
from shuup.core.signals import context_cache_item_bumped, order_changed
from shuup.core.utils import context_cache
from shuup.core.utils.context_cache import (
    bump_internal_cache,
    bump_product_signal_handler,
    bump_shop_product_signal_handler,
)
from shuup.core.utils.db import extend_sqlite_functions
from shuup.core.utils.price_cache import bump_all_price_caches, bump_prices_for_product, bump_prices_for_shop_product


@receiver(post_migrate)
def on_migrate(sender, **kwargs):
    from .models import SupplierModule

    SupplierModule.ensure_all_supplier_modules()


def handle_post_save_bump_all_prices_caches(sender, instance, **kwargs):
    # bump all the prices for all the shops, as it is impossible to know
    # from which shop things have changed
    bump_all_price_caches()


def handle_product_post_save(sender, instance, **kwargs):
    bump_product_signal_handler(sender, instance, **kwargs)
    bump_prices_for_product(instance)

    for shop_id in set(instance.shop_products.all().values_list("shop_id", flat=True)):
        context_cache_item_bumped.send(sender=Shop, shop_id=shop_id)


def handle_shop_product_post_save(sender, instance, **kwargs):
    if isinstance(instance, Category):
        bump_shop_product_signal_handler(sender, instance.shop_products.all().values_list("pk", flat=True), **kwargs)

        for shop_id in set(instance.shop_products.all().values_list("shop_id", flat=True)):
            bump_prices_for_shop_product(shop_id)
            context_cache_item_bumped.send(sender=Shop, shop_id=shop_id)
    else:  # ShopProduct
        bump_shop_product_signal_handler(sender, instance, **kwargs)
        bump_prices_for_shop_product(instance.shop_id)
        context_cache_item_bumped.send(sender=Shop, shop_id=instance.shop_id)


def handle_supplier_post_save(sender, instance, **kwargs):
    bump_shop_product_signal_handler(sender, instance.shop_products.all().values_list("pk", flat=True), **kwargs)

    for shop_id in set(instance.shop_products.all().values_list("shop_id", flat=True)):
        bump_prices_for_shop_product(shop_id)
        context_cache_item_bumped.send(sender=Shop, shop_id=shop_id)


def handle_contact_post_save(sender, instance, **kwargs):
    bump_internal_cache()
    get_groups_ids.cache_clear()


@receiver(order_creator_finished)
def on_order_creator_finished(sender, order, source, **kwargs):
    # reset product prices
    for product_id, shop_id in order.lines.exclude(product__isnull=False).values_list("product_id", "order__shop_id"):
        context_cache.bump_cache_for_product(product_id, shop_id)


@receiver(order_changed)
def on_order_changed(sender, order, **kwargs):
    for line in order.lines.products().only("product_id", "supplier").select_related("supplier"):
        line.supplier.update_stock(line.product_id)


def handle_contact_group_price_display_post_save(sender, instance, **kwargs):
    get_price_display_options.cache_clear()


def handle_display_unit_post_save(sender, instance, **kwargs):
    get_display_unit.cache_clear()


# connect signals to bump caches on Product and ShopProduct change
m2m_changed.connect(
    handle_shop_product_post_save, sender=ShopProduct.categories.through, dispatch_uid="shop_product:change_categories"
)
post_save.connect(handle_product_post_save, sender=Product, dispatch_uid="product:bump_product_cache")
post_save.connect(
    handle_shop_product_post_save, sender=ShopProduct, dispatch_uid="shop_product:bump_shop_product_cache"
)

# connect signals to bump caches on Supplier change
post_save.connect(handle_supplier_post_save, sender=Supplier, dispatch_uid="supplier:bump_supplier_cache")

# connect signals to bump price caches on Tax and TaxClass change
post_save.connect(handle_post_save_bump_all_prices_caches, sender=Tax, dispatch_uid="tax_class:bump_prices_cache")
post_save.connect(handle_post_save_bump_all_prices_caches, sender=TaxClass, dispatch_uid="tax_class:bump_prices_cache")

# connect signals to bump context cache internal cache for contacts
post_save.connect(handle_contact_post_save, sender=PersonContact, dispatch_uid="person_contact:bump_context_cache")
post_save.connect(handle_contact_post_save, sender=CompanyContact, dispatch_uid="company_contact:bump_context_cache")
m2m_changed.connect(
    handle_contact_post_save, sender=ContactGroup.members.through, dispatch_uid="contact_group:change_members"
)

post_save.connect(
    handle_contact_group_price_display_post_save,
    sender=ContactGroupPriceDisplay,
    dispatch_uid="shuup_contact_group_price_display_bump",
)

post_save.connect(handle_display_unit_post_save, sender=DisplayUnit, dispatch_uid="shuup_display_unit_bump")

connection_created.connect(extend_sqlite_functions)
