# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json
import pytest
from django.test import override_settings
from django.utils.translation import activate
from jinja2 import Environment
from jinja2.runtime import Context

from shuup.admin.menu import PRODUCTS_MENU_CATEGORY, SETTINGS_MENU_CATEGORY, get_menu_entry_categories
from shuup.admin.modules.menu.views.arrange import SupplierMenuArrangeView, SupplierMenuResetView
from shuup.admin.template_helpers.shuup_admin import is_menu_category_active, is_menu_item_active
from shuup.admin.utils.permissions import set_permissions_for_group
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import reverse


def get_staff_user():
    shop = factories.get_default_shop()
    staff_user = factories.UserFactory(is_staff=True)
    permission_group = factories.get_default_permission_group()
    staff_user.groups.add(permission_group)
    shop.staff_members.add(staff_user)
    set_permissions_for_group(
        permission_group, ["Customize Staff Admin Menu", "menu.arrange_staff", "menu.reset_staff"]
    )
    return staff_user


def get_supplier_user():
    factories.get_default_shop()
    supplier = factories.get_default_supplier()
    supplier_user = factories.UserFactory(is_staff=True)
    permission_group = factories.get_default_permission_group()
    supplier_user.groups.add(permission_group)
    set_permissions_for_group(
        permission_group, ["Customize Supplier Admin Menu", "menu.arrange_supplier", "menu.reset_staff"]
    )
    return supplier_user


def test_menu_arrange_view(rf):
    with override_settings(
        SHUUP_ADMIN_SHOP_PROVIDER_SPEC="shuup.testing.shop_provider.TestingAdminShopProvider",
        SHUUP_ADMIN_SUPPLIER_PROVIDER_SPEC="shuup.testing.supplier_provider.FirstSupplierProvider",
    ):
        supplier_user = get_supplier_user()
        url = reverse("shuup_admin:menu.arrange_supplier")
        request = apply_request_middleware(rf.get(url), user=supplier_user)
        response = SupplierMenuArrangeView.as_view()(request)
        assert response.status_code == 200


@pytest.mark.django_db
def test_menu_save_arrange_view(rf):
    with override_settings(
        SHUUP_ADMIN_SHOP_PROVIDER_SPEC="shuup.testing.shop_provider.TestingAdminShopProvider",
        SHUUP_ADMIN_SUPPLIER_PROVIDER_SPEC="shuup.testing.supplier_provider.FirstSupplierProvider",
    ):
        supplier_user = get_supplier_user()
        url = reverse("shuup_admin:menu.arrange_supplier")

        menu_request = apply_request_middleware(rf.get(url), user=supplier_user)
        admin_menu_before_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
        new_data = admin_menu_before_save[::-1]
        new_data[0]["entries"][0]["name"] = "Menu Arrange"
        data = {"menus": json.dumps(new_data)}

        request = apply_request_middleware(rf.post(url, data=data), user=supplier_user)
        response = SupplierMenuArrangeView.as_view()(request)
        assert response.status_code == 302

        menu_request = apply_request_middleware(rf.get(url), user=supplier_user)
        admin_menu_after_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
        assert admin_menu_after_save == new_data

        # Make sure other staff has same menu after save
        another_supplier_user = get_supplier_user()
        menu_request = apply_request_middleware(rf.get(url), user=supplier_user)
        admin_menu_after_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
        assert admin_menu_after_save == new_data

        # Test that different languages are also customizable
        activate("fi")
        new_data[0]["entries"][0]["name"] = "Listan jarjestaminen"
        data = {"menus": json.dumps(new_data)}
        request = apply_request_middleware(rf.post(url, data=data), user=supplier_user)
        response = SupplierMenuArrangeView.as_view()(request)
        assert response.status_code == 302

        menu_request = apply_request_middleware(rf.get(url), user=supplier_user)
        admin_menu_after_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
        assert admin_menu_after_save == new_data

        # Back in english menu title should still be "Menu Arrange"
        activate("en")
        menu_request = apply_request_middleware(rf.get(url), user=supplier_user)
        admin_menu_after_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
        assert admin_menu_after_save[0]["entries"][0]["name"] == "Menu Arrange"

    # Make sure staff does not receive this menu as long as the get_supplier provider
    # returns None which is the default
    staff = get_staff_user()
    menu_request = apply_request_middleware(rf.get(url), user=staff)
    staff_menu = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
    assert staff_menu != admin_menu_after_save


@pytest.mark.django_db
def test_menu_reset_view(rf):
    with override_settings(
        SHUUP_ADMIN_SHOP_PROVIDER_SPEC="shuup.testing.shop_provider.TestingAdminShopProvider",
        SHUUP_ADMIN_SUPPLIER_PROVIDER_SPEC="shuup.testing.supplier_provider.FirstSupplierProvider",
    ):
        supplier_user = get_supplier_user()
        arrange_url = reverse("shuup_admin:menu.arrange_supplier")
        menu_request = apply_request_middleware(rf.get(arrange_url), user=supplier_user)
        admin_menu_before_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
        new_data = [m.to_dict() for m in get_menu_entry_categories(menu_request)][::-1]
        new_data[0]["entries"][0]["name"] = "Menu Arrange"
        data = {"menus": json.dumps(new_data)}
        SupplierMenuArrangeView.as_view()(apply_request_middleware(rf.post(arrange_url, data=data), user=supplier_user))
        admin_menu_after_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
        assert admin_menu_after_save == new_data

        reset_url = reverse("shuup_admin:menu.reset_supplier")
        request = apply_request_middleware(rf.get(reset_url), user=supplier_user)
        response = SupplierMenuResetView.as_view()(request)
        assert response.status_code == 302
        admin_menu_after_reset = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
        assert admin_menu_after_reset == admin_menu_before_save
