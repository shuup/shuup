# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shoop.admin.menu import get_menu_entry_categories
from shoop.admin.module_registry import get_modules, replace_modules
from shoop.admin.utils.permissions import (
    get_default_model_permissions, get_permission_object_from_string,
    get_permissions_from_urls
)
from shoop.core.models import Product
from shoop_tests.admin.fixtures.test_module import ARestrictedTestModule
from shoop_tests.utils.faux_users import StaffUser


def test_default_model_permissions():
    permissions = set(["shoop.add_product", "shoop.delete_product", "shoop.change_product"])

    assert get_default_model_permissions(Product) == permissions


def test_permissions_for_menu_entries(rf, admin_user):
    permissions = set(["shoop.add_product", "shoop.delete_product", "shoop.change_product"])

    request = rf.get("/")
    request.user = StaffUser()
    request.user.permissions = permissions

    with replace_modules([ARestrictedTestModule]):
        modules = [m for m in get_modules()]
        assert request.user.permissions == modules[0].get_required_permissions()

        categories = get_menu_entry_categories(request)
        assert categories

        # Make sure category is displayed if user has correct permissions
        test_category_menu_entries = categories.get("RestrictedTest")
        assert any(me.text == "OK" for me in test_category_menu_entries)

        # No menu items should be displayed if user has no permissions
        request.user.permissions = []
        categories = get_menu_entry_categories(request)
        assert not categories


@pytest.mark.django_db
def test_valid_permissions_for_all_modules():
    """
    If a module requires permissions, make sure all url and module-
    level permissions are valid.
    """
    for module in get_modules():
        url_permissions = set(get_permissions_from_urls(module.get_urls()))
        module_permissions = set(module.get_required_permissions())
        for permission in (url_permissions | module_permissions):
            assert get_permission_object_from_string(permission)
