# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from shuup.core.excs import (
    ProductNotOrderableProblem, ProductNotVisibleProblem
)
from shuup.core.models import (
    AnonymousContact, get_person_contact, ProductVisibility,
    ShopProductVisibility, Supplier
)
from shuup.testing.factories import (
    get_default_customer_group, get_default_product, get_default_shop,
    get_default_shop_product, get_default_supplier
)
from shuup_tests.core.utils import modify
from shuup_tests.utils import (
    error_does_not_exist, error_exists, printable_gibberish
)
from shuup_tests.utils.fixtures import regular_user


@pytest.mark.django_db
def test_image_inheritance():
    shop = get_default_shop()
    product = get_default_product()
    shop_product = product.get_shop_instance(shop)
    assert product.primary_image_id
    assert shop_product.primary_image == product.primary_image


@pytest.mark.django_db
def test_product_orderability():
    anon_contact = AnonymousContact()
    shop_product = get_default_shop_product()
    supplier = get_default_supplier()

    with modify(shop_product, visibility_limit=ProductVisibility.VISIBLE_TO_ALL, orderable=True):
        shop_product.raise_if_not_orderable(supplier=supplier, customer=anon_contact, quantity=1)
        assert shop_product.is_orderable(supplier=supplier, customer=anon_contact, quantity=1)

    with modify(shop_product, visibility_limit=ProductVisibility.VISIBLE_TO_LOGGED_IN, orderable=True):
        with pytest.raises(ProductNotOrderableProblem):
            shop_product.raise_if_not_orderable(supplier=supplier, customer=anon_contact, quantity=1)
        assert not shop_product.is_orderable(supplier=supplier, customer=anon_contact, quantity=1)


@pytest.mark.django_db
def test_product_minimum_order_quantity(admin_user):
    shop_product = get_default_shop_product()
    supplier = get_default_supplier()
    admin_contact = get_person_contact(admin_user)

    with modify(shop_product, visibility_limit=ProductVisibility.VISIBLE_TO_ALL, orderable=True, minimum_purchase_quantity=10):
        assert any(ve.code == "purchase_quantity_not_met" for ve in shop_product.get_orderability_errors(supplier=supplier, customer=admin_contact, quantity=1))
        assert not any(ve.code == "purchase_quantity_not_met" for ve in shop_product.get_orderability_errors(supplier=supplier, customer=admin_contact, quantity=15))


@pytest.mark.django_db
def test_product_order_multiple(admin_user):
    shop_product = get_default_shop_product()
    supplier = get_default_supplier()
    admin_contact = get_person_contact(admin_user)

    with modify(shop_product, visibility_limit=ProductVisibility.VISIBLE_TO_ALL, orderable=True, purchase_multiple=7):
        assert any(ve.code == "invalid_purchase_multiple" for ve in shop_product.get_orderability_errors(supplier=supplier, customer=admin_contact, quantity=4))
        assert any(ve.code == "invalid_purchase_multiple" for ve in shop_product.get_orderability_errors(supplier=supplier, customer=admin_contact, quantity=25))
        assert not any(ve.code == "invalid_purchase_multiple" for ve in shop_product.get_orderability_errors(supplier=supplier, customer=admin_contact, quantity=49))


@pytest.mark.django_db
def test_product_unsupplied(admin_user):
    shop_product = get_default_shop_product()
    fake_supplier = Supplier.objects.create(identifier="fake")
    admin_contact = get_person_contact(admin_user)

    with modify(shop_product, visibility_limit=ProductVisibility.VISIBLE_TO_ALL, orderable=True):
        assert any(ve.code == "invalid_supplier" for ve in shop_product.get_orderability_errors(supplier=fake_supplier, customer=admin_contact, quantity=1))

@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_product_visibility(rf, admin_user, regular_user):
    anon_contact = get_person_contact(AnonymousUser())
    shop_product = get_default_shop_product()
    admin_contact = get_person_contact(admin_user)
    regular_contact = get_person_contact(regular_user)


    with modify(shop_product.product, deleted=True):  # NB: assigning to `product` here works because `get_shop_instance` populates `_product_cache`
        assert error_exists(shop_product.get_visibility_errors(customer=anon_contact), "product_deleted")
        assert error_exists(shop_product.get_visibility_errors(customer=admin_contact), "product_deleted")
        with pytest.raises(ProductNotVisibleProblem):
            shop_product.raise_if_not_visible(anon_contact)
        assert not shop_product.is_list_visible()

    with modify(shop_product, visibility_limit=ProductVisibility.VISIBLE_TO_ALL, visibility=ShopProductVisibility.NOT_VISIBLE):
        assert error_exists(shop_product.get_visibility_errors(customer=anon_contact), "product_not_visible")
        assert error_does_not_exist(shop_product.get_visibility_errors(customer=admin_contact), "product_not_visible")
        assert not shop_product.is_list_visible()

    with modify(shop_product, visibility_limit=ProductVisibility.VISIBLE_TO_LOGGED_IN, visibility=ShopProductVisibility.ALWAYS_VISIBLE):
        assert error_exists(shop_product.get_visibility_errors(customer=anon_contact), "product_not_visible_to_anonymous")
        assert error_does_not_exist(shop_product.get_visibility_errors(customer=admin_contact), "product_not_visible_to_anonymous")

    customer_group = get_default_customer_group()
    grouped_user = get_user_model().objects.create_user(username=printable_gibberish(20))
    grouped_contact = get_person_contact(grouped_user)
    with modify(shop_product, visibility_limit=ProductVisibility.VISIBLE_TO_GROUPS, visibility=ShopProductVisibility.ALWAYS_VISIBLE):
        shop_product.visibility_groups.add(customer_group)
        customer_group.members.add(grouped_contact)
        customer_group.members.remove(get_person_contact(regular_user))
        assert error_does_not_exist(shop_product.get_visibility_errors(customer=grouped_contact), "product_not_visible_to_group")
        assert error_does_not_exist(shop_product.get_visibility_errors(customer=admin_contact), "product_not_visible_to_group")
        assert error_exists(shop_product.get_visibility_errors(customer=regular_contact), "product_not_visible_to_group")
