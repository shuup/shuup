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
from shuup.admin.modules.menu.views.arrange import StaffMenuArrangeView, StaffMenuResetView
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


def test_menu_arrange_view(rf):
    staff_user = get_staff_user()
    url = reverse("shuup_admin:menu.arrange_staff")
    request = apply_request_middleware(rf.get(url), user=staff_user)
    response = StaffMenuArrangeView.as_view()(request)
    assert response.status_code == 200


@pytest.mark.django_db
def test_menu_save_arrange_view(rf):
    staff_user = get_staff_user()
    url = reverse("shuup_admin:menu.arrange_staff")

    menu_request = apply_request_middleware(rf.get(url), user=staff_user)
    admin_menu_before_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
    new_data = admin_menu_before_save[::-1]
    new_data[0]["entries"][0]["name"] = "Menu Arrange"
    data = {"menus": json.dumps(new_data)}

    request = apply_request_middleware(rf.post(url, data=data), user=staff_user)
    response = StaffMenuArrangeView.as_view()(request)
    assert response.status_code == 302

    menu_request = apply_request_middleware(rf.get(url), user=staff_user)
    admin_menu_after_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
    assert admin_menu_after_save == new_data

    # Make sure other staff has same menu after save
    another_staff_user = get_staff_user()
    menu_request = apply_request_middleware(rf.get(url), user=staff_user)
    admin_menu_after_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
    assert admin_menu_after_save == new_data

    # Test that different languages are also customizable
    activate("fi")
    new_data[0]["entries"][0]["name"] = "Listan jarjestaminen"
    data = {"menus": json.dumps(new_data)}
    request = apply_request_middleware(rf.post(url, data=data), user=staff_user)
    response = StaffMenuArrangeView.as_view()(request)
    assert response.status_code == 302

    menu_request = apply_request_middleware(rf.get(url), user=staff_user)
    admin_menu_after_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
    assert admin_menu_after_save == new_data

    # Back in english menu title should still be "Menu Arrange"
    activate("en")
    menu_request = apply_request_middleware(rf.get(url), user=staff_user)
    admin_menu_after_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
    assert admin_menu_after_save[0]["entries"][0]["name"] == "Menu Arrange"


@pytest.mark.django_db
def test_menu_reset_view(rf):
    staff_user = get_staff_user()
    arrange_url = reverse("shuup_admin:menu.arrange_staff")
    menu_request = apply_request_middleware(rf.get(arrange_url), user=staff_user)
    admin_menu_before_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
    new_data = [m.to_dict() for m in get_menu_entry_categories(menu_request)][::-1]
    new_data[0]["entries"][0]["name"] = "Menu Arrange"
    data = {"menus": json.dumps(new_data)}
    StaffMenuArrangeView.as_view()(apply_request_middleware(rf.post(arrange_url, data=data), user=staff_user))
    admin_menu_after_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
    assert admin_menu_after_save == new_data

    reset_url = reverse("shuup_admin:menu.reset_staff")
    request = apply_request_middleware(rf.get(reset_url), user=staff_user)
    response = StaffMenuResetView.as_view()(request)
    assert response.status_code == 302
    admin_menu_after_reset = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
    assert admin_menu_after_reset == admin_menu_before_save
