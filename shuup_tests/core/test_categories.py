# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from filer.models import Folder, Image

from shuup import configuration
from shuup.core.models import (
    AnonymousContact,
    Category,
    CategoryStatus,
    CategoryVisibility,
    ContactGroup,
    get_person_contact,
)
from shuup.testing.factories import (
    DEFAULT_NAME,
    get_all_seeing_key,
    get_default_category,
    get_default_shop,
    get_default_shop_product,
)
from shuup_tests.utils.fixtures import regular_user


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_category_visibility(admin_user, regular_user):
    visible_public_category = Category.objects.create(
        status=CategoryStatus.VISIBLE,
        visibility=CategoryVisibility.VISIBLE_TO_ALL,
        identifier="visible_public",
        name=DEFAULT_NAME,
    )
    hidden_public_category = Category.objects.create(
        status=CategoryStatus.INVISIBLE,
        visibility=CategoryVisibility.VISIBLE_TO_ALL,
        identifier="hidden_public",
        name=DEFAULT_NAME,
    )
    deleted_public_category = Category.objects.create(
        status=CategoryStatus.DELETED,
        visibility=CategoryVisibility.VISIBLE_TO_ALL,
        identifier="deleted_public",
        name=DEFAULT_NAME,
    )
    logged_in_category = Category.objects.create(
        status=CategoryStatus.VISIBLE,
        visibility=CategoryVisibility.VISIBLE_TO_LOGGED_IN,
        identifier="visible_logged_in",
        name=DEFAULT_NAME,
    )
    group_visible_category = Category.objects.create(
        status=CategoryStatus.VISIBLE,
        visibility=CategoryVisibility.VISIBLE_TO_GROUPS,
        identifier="visible_groups",
        name=DEFAULT_NAME,
    )

    assert visible_public_category.name == DEFAULT_NAME
    assert str(visible_public_category) == DEFAULT_NAME

    anon_contact = AnonymousContact()
    regular_contact = get_person_contact(regular_user)
    admin_contact = get_person_contact(admin_user)

    configuration.set(None, get_all_seeing_key(admin_contact), True)

    for (customer, category, expect) in [
        (anon_contact, visible_public_category, True),
        (anon_contact, hidden_public_category, False),
        (anon_contact, deleted_public_category, False),
        (anon_contact, logged_in_category, False),
        (anon_contact, group_visible_category, False),
        (regular_contact, visible_public_category, True),
        (regular_contact, hidden_public_category, False),
        (regular_contact, deleted_public_category, False),
        (regular_contact, logged_in_category, True),
        (regular_contact, group_visible_category, False),
        (admin_contact, visible_public_category, True),
        (admin_contact, hidden_public_category, True),
        (admin_contact, deleted_public_category, False),
        (admin_contact, logged_in_category, True),
        (admin_contact, group_visible_category, True),
    ]:
        result = Category.objects.all_visible(customer=customer).filter(pk=category.pk).exists()
        assert result == expect, "Queryset visibility of %s for %s as expected" % (category.identifier, customer)
        assert category.is_visible(customer) == expect, "Direct visibility of %s for %s as expected" % (
            category.identifier,
            customer,
        )

    assert (
        not Category.objects.all_except_deleted().filter(pk=deleted_public_category.pk).exists()
    ), "Deleted category does not show up in 'all_except_deleted'"
    configuration.set(None, get_all_seeing_key(admin_contact), False)


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_category_group_visibilities(regular_user):
    shop = get_default_shop()
    regular_contact = get_person_contact(regular_user)
    silver_group = ContactGroup.objects.create(identifier="silver", shop=shop)
    diamond_group = ContactGroup.objects.create(identifier="gold", shop=shop)
    regular_contact.groups.add(silver_group)

    silvers = Category.objects.create(
        status=CategoryStatus.VISIBLE,
        visibility=CategoryVisibility.VISIBLE_TO_GROUPS,
        identifier="silver_groups",
        name="Silvers",
    )
    silvers.visibility_groups.add(regular_contact.get_default_group(), silver_group)

    diamonds = Category.objects.create(
        status=CategoryStatus.VISIBLE,
        visibility=CategoryVisibility.VISIBLE_TO_GROUPS,
        identifier="silver_and_diamonds_groups",
        name="Diamonds",
    )
    diamonds.visibility_groups.add(diamond_group)

    # Multiple groups for contact should not cause duplicate results
    assert Category.objects.all_visible(customer=regular_contact).count() == 1

    regular_contact.groups.add(diamond_group)
    assert Category.objects.all_visible(customer=regular_contact).count() == 2


@pytest.mark.django_db
def test_category_wont_be_deleted():
    category = Category.objects.create(
        status=CategoryStatus.VISIBLE,
        visibility=CategoryVisibility.VISIBLE_TO_ALL,
        identifier="visible_public",
        name=DEFAULT_NAME,
    )

    folder = Folder.objects.create(name="Root")
    img = Image.objects.create(name="imagefile", folder=folder)

    category.image = img
    category.save()
    img.delete()

    Category.objects.get(pk=category.pk)


@pytest.mark.django_db
def test_category_deletion(admin_user):
    admin = get_person_contact(admin_user)
    category = get_default_category()
    category.children.create(identifier="foo")
    shop_product = get_default_shop_product()
    shop_product.categories.add(category)
    shop_product.primary_category = category
    shop_product.save()

    configuration.set(None, get_all_seeing_key(admin), True)

    assert category.status == CategoryStatus.VISIBLE
    assert category.children.count() == 1

    with pytest.raises(NotImplementedError):
        category.delete()

    category.soft_delete()
    shop_product.refresh_from_db()
    shop_product.product.refresh_from_db()

    assert shop_product.categories.count() == 0
    assert shop_product.primary_category is None
    assert category.status == CategoryStatus.DELETED
    assert category.children.count() == 0
    # the child category still exists
    assert Category.objects.all_visible(customer=admin).count() == 1
    assert Category.objects.all_except_deleted().count() == 1
    configuration.set(None, get_all_seeing_key(admin), False)


@pytest.mark.django_db
def test_category_cached_children(admin_user):
    parent = Category.objects.create(name="Parent")
    child1 = Category.objects.create(name="Child1", parent=parent)
    child2 = Category.objects.create(name="Child2", parent=parent)
    child3 = Category.objects.create(name="Child3", parent=parent)

    for cache_test in range(2):
        children = parent.get_cached_children()
        assert children[0] == child1
        assert children[1] == child2
        assert children[2] == child3
