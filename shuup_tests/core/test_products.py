# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import pytest
from datetime import timedelta
from django.utils.timezone import now

from shuup import configuration
from shuup.core.models import AnonymousContact, Product, ProductVisibility, ShopProductVisibility, get_person_contact
from shuup.testing.factories import (
    create_product,
    get_all_seeing_key,
    get_default_customer_group,
    get_default_shop,
    get_default_shop_product,
    get_default_supplier,
)


@pytest.mark.parametrize(
    "visibility,show_in_list,show_in_search",
    [
        (ShopProductVisibility.NOT_VISIBLE, False, False),
        (ShopProductVisibility.SEARCHABLE, False, True),
        (ShopProductVisibility.LISTED, True, False),
        (ShopProductVisibility.ALWAYS_VISIBLE, True, True),
    ],
)
@pytest.mark.django_db
def test_product_query(visibility, show_in_list, show_in_search, admin_user, regular_user):
    shop = get_default_shop()
    supplier = get_default_supplier(shop)
    product = create_product("test-sku", shop=shop, supplier=supplier)
    shop_product = product.get_shop_instance(shop)
    anon_contact = AnonymousContact()
    get_person_contact(regular_user)
    admin_contact = get_person_contact(admin_user)

    shop_product.visibility = visibility
    shop_product.save()

    assert shop_product.visibility_limit == ProductVisibility.VISIBLE_TO_ALL

    # Anonymous contact should be the same as no contact
    assert (product in Product.objects.listed(shop=shop)) == show_in_list
    assert (product in Product.objects.searchable(shop=shop)) == show_in_search
    assert (product in Product.objects.listed(shop=shop, customer=anon_contact)) == show_in_list
    assert (product in Product.objects.searchable(shop=shop, customer=anon_contact)) == show_in_search

    # Admin should see all non-deleted results
    configuration.set(None, get_all_seeing_key(admin_contact), True)
    assert product in Product.objects.listed(shop=shop, customer=admin_contact)
    assert product in Product.objects.searchable(shop=shop, customer=admin_contact)

    # Anonymous contact shouldn't see products with logged in visibility limit
    shop_product.visibility_limit = ProductVisibility.VISIBLE_TO_LOGGED_IN
    shop_product.save()
    assert product not in Product.objects.listed(shop=shop, customer=anon_contact)
    assert product not in Product.objects.searchable(shop=shop, customer=anon_contact)

    # Reset visibility limit
    shop_product.visibility_limit = ProductVisibility.VISIBLE_TO_ALL
    shop_product.save()

    # No one should see deleted products
    product.soft_delete()
    assert product not in Product.objects.listed(shop=shop)
    assert product not in Product.objects.searchable(shop=shop)
    assert product not in Product.objects.listed(shop=shop, customer=admin_contact)
    assert product not in Product.objects.searchable(shop=shop, customer=admin_contact)
    configuration.set(None, get_all_seeing_key(admin_contact), False)


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_product_query_with_group_visibility(regular_user):
    default_group = get_default_customer_group()
    shop_product = get_default_shop_product()
    shop_product.visibility_limit = 3
    shop_product.save()
    shop = shop_product.shop
    product = shop_product.product
    shop_product.visibility_groups.add(default_group)
    regular_contact = get_person_contact(regular_user)

    assert not Product.objects.listed(shop=shop, customer=regular_contact).filter(pk=product.pk).exists()
    regular_contact.groups.add(default_group)
    assert Product.objects.listed(shop=shop, customer=regular_contact).filter(pk=product.pk).count() == 1

    shop_product.visibility_groups.add(regular_contact.get_default_group())
    # Multiple visibility groups for shop product shouldn't cause duplicate matches
    assert Product.objects.listed(shop=shop, customer=regular_contact).filter(pk=product.pk).count() == 1


@pytest.mark.django_db
def test_get_prices_children(rf, regular_user):
    shop = get_default_shop()
    parent = create_product("parent", shop, get_default_supplier())
    child = create_product("child-no-shop")
    child.link_to_parent(parent)

    request = rf.get("/")
    request.shop = shop
    request.customer = get_person_contact(regular_user)

    parent.refresh_from_db()
    prices = parent.get_priced_children(request)
    assert len(prices) == 0

    child_with_shop = create_product("child-shop", shop, get_default_supplier(), 10)
    child_with_shop.link_to_parent(parent)
    parent.refresh_from_db()
    prices = parent.get_priced_children(request)
    assert len(prices) == 1


@pytest.mark.parametrize(
    "available_until,visible",
    [
        (now() + timedelta(days=2), True),
        (now() - timedelta(days=2), False),
    ],
)
@pytest.mark.django_db
def test_product_available(admin_user, regular_user, available_until, visible):
    shop = get_default_shop()
    supplier = get_default_supplier(shop)
    product = create_product("test-sku", shop=shop, supplier=supplier)
    shop_product = product.get_shop_instance(shop)
    regular_contact = get_person_contact(regular_user)
    admin_contact = get_person_contact(admin_user)

    shop_product.available_until = available_until
    shop_product.save()

    assert (product in Product.objects.listed(shop=shop)) == visible
    assert (product in Product.objects.searchable(shop=shop)) == visible
    assert (product in Product.objects.listed(shop=shop, customer=admin_contact)) == visible
    assert (product in Product.objects.searchable(shop=shop, customer=admin_contact)) == visible
    assert (product in Product.objects.searchable(shop=shop, customer=regular_contact)) == visible

    configuration.set(None, get_all_seeing_key(admin_contact), True)
    assert product in Product.objects.listed(shop=shop, customer=admin_contact)
    assert product in Product.objects.searchable(shop=shop, customer=admin_contact)
    configuration.set(None, get_all_seeing_key(admin_contact), False)
