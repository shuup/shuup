# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import django
import pytest
import six
from django.contrib.auth.models import AbstractUser, Group

from shuup.admin.menu import get_menu_entry_categories
from shuup.admin.module_registry import get_modules, replace_modules
from shuup.admin.modules.customers_dashboard import CustomersDashboardModule
from shuup.admin.modules.sales_dashboard import SalesDashboardModule
from shuup.admin.toolbar import (
    DropdownActionButton,
    DropdownItem,
    JavaScriptActionButton,
    NewActionButton,
    PostActionButton,
    SettingsActionButton,
    URLActionButton,
)
from shuup.admin.utils.permissions import (
    get_default_model_permissions,
    get_missing_permissions,
    get_permission_object_from_string,
    get_permissions_from_urls,
    set_permissions_for_group,
)
from shuup.core.models import Product, ShopProduct
from shuup.testing import factories
from shuup.utils.django_compat import reverse, reverse_lazy
from shuup_tests.admin.fixtures.test_module import ARestrictedTestModule
from shuup_tests.utils.faux_users import StaffUser

migrated_permissions = {
    CustomersDashboardModule: ("shuup.view_customers_dashboard"),
    SalesDashboardModule: ("shuup.view_sales_dashboard"),
}


def test_default_model_permissions():
    permissions = set(["shuup.add_product", "shuup.delete_product", "shuup.change_product", "shuup.view_product"])
    assert get_default_model_permissions(Product) == permissions


def test_permissions_for_menu_entries(rf, admin_user):
    request = rf.get("/")
    request.user = factories.get_default_staff_user()
    permission_group = request.user.groups.first()
    set_permissions_for_group(
        permission_group, set("dashboard") | set(ARestrictedTestModule().get_required_permissions())
    )

    with replace_modules([ARestrictedTestModule]):
        categories = get_menu_entry_categories(request)
        assert categories

        # Make sure category is displayed if user has correct permissions
        test_category_menu_entries = [cat for cat in categories if cat.name == "RestrictedTest"][0]
        assert any(me.text == "OK" for me in test_category_menu_entries)

        # No menu items should be displayed if user has no permissions
        set_permissions_for_group(permission_group, set())
        categories = get_menu_entry_categories(request)
        assert not categories


@pytest.mark.django_db
def test_valid_permissions_for_all_modules():
    """
    If a module requires permissions, make sure all url and module-
    level permissions are valid.

    Modules that add permissions using migrations must be checked
    manually since their permissions will not be in the test database.
    """
    for module in get_modules():
        url_permissions = set(get_permissions_from_urls(module.get_urls()))
        module_permissions = set(module.get_required_permissions())
        for permission in url_permissions | module_permissions:
            # Only requirement for permissions are that they
            # are list of strings
            assert isinstance(permission, six.string_types)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "button_class, kwargs",
    [
        (URLActionButton, {"url": "/test/url/"}),
        (JavaScriptActionButton, {"onclick": None}),
        (PostActionButton, {}),
        (DropdownActionButton, {"items": [DropdownItem()]}),
        (DropdownItem, {}),
    ],
)
def test_toolbar_button_permissions(rf, button_class, kwargs):
    permissions = set(["shuup.add_product", "shuup.delete_product", "shuup.change_product"])

    request = rf.get("/")
    request.user = factories.get_default_staff_user()
    button = button_class(required_permissions=permissions, **kwargs)
    rendered_button = "".join(bit for bit in button.render(request))
    assert not rendered_button

    # Set permissions for the user
    set_permissions_for_group(request.user.groups.first(), permissions)
    rendered_button = "".join(bit for bit in button.render(request))
    assert rendered_button


@pytest.mark.parametrize(
    "button, permission, instance",
    [
        (URLActionButton(url=reverse("shuup_admin:shop_product.new")), "shop_product.new", URLActionButton),
        (URLActionButton(url=reverse_lazy("shuup_admin:shop_product.new")), "shop_product.new", URLActionButton),
        (NewActionButton.for_model(ShopProduct), "shop_product.new", URLActionButton),
        (SettingsActionButton.for_model(ShopProduct, return_url="/"), "shop_product.list_settings", URLActionButton),
        # for_model without shuup_admin url returns None
        (NewActionButton.for_model(AbstractUser), "abstract_user.new", type(None)),
        (SettingsActionButton.for_model(AbstractUser), "abstract_user.list_settings", type(None)),
    ],
)
def test_url_buttons_permission(rf, button, permission, instance):
    request = rf.get("/")

    assert isinstance(button, instance)

    if button is not None:
        request.user = factories.get_default_staff_user()
        assert not "".join(bit for bit in button.render(request))

        set_permissions_for_group(request.user.groups.first(), (permission,))
        assert "".join(bit for bit in button.render(request))


@pytest.mark.django_db
def test_user_permission_cache_bump(rf):
    user = factories.get_default_staff_user()
    group_a = Group.objects.create(name="Group A")
    group_b = Group.objects.create(name="Group B")

    group_a_permissions = ["purchase", "sell"]
    group_b_permissions = ["delete", "create"]
    set_permissions_for_group(group_a, set(group_a_permissions))
    set_permissions_for_group(group_b, set(group_b_permissions))
    all_permissions = set(group_a_permissions + group_b_permissions)

    # as user is not in any group, it misses all the groups
    assert get_missing_permissions(user, all_permissions) == all_permissions

    # add the user to Group A
    user.groups.add(group_a)
    # the user misses the group_b permissions
    assert get_missing_permissions(user, all_permissions) == set(group_b_permissions)

    # make the user be part only of group b
    group_b.user_set.add(user)
    group_a.user_set.remove(user)
    # the user misses the group_a permissions
    assert get_missing_permissions(user, all_permissions) == set(group_a_permissions)

    # user is part of all groups
    user.groups.set([group_a, group_b])
    assert get_missing_permissions(user, all_permissions) == set()
