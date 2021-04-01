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
from jinja2 import Environment
from jinja2.runtime import Context

from shuup.admin.menu import PRODUCTS_MENU_CATEGORY, SETTINGS_MENU_CATEGORY, get_menu_entry_categories
from shuup.admin.modules.menu.views.arrange import AdminMenuArrangeView, AdminMenuResetView
from shuup.admin.template_helpers.shuup_admin import is_menu_category_active, is_menu_item_active
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import reverse


def test_menu_arrange_view(rf, admin_user):
    url = reverse("shuup_admin:menu.arrange")
    request = apply_request_middleware(rf.get(url), user=admin_user)
    response = AdminMenuArrangeView.as_view()(request)
    assert response.status_code == 200


@pytest.mark.django_db
def test_menu_save_arrange_view(rf, admin_user):
    url = reverse("shuup_admin:menu.arrange")

    menu_request = apply_request_middleware(rf.get(url), user=admin_user)
    admin_menu_before_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
    data = {"menus": json.dumps(admin_menu_before_save[::-1])}
    request = apply_request_middleware(rf.post(url, data=data), user=admin_user)
    response = AdminMenuArrangeView.as_view()(request)
    assert response.status_code == 302

    menu_request = apply_request_middleware(rf.get(url), user=admin_user)
    admin_menu_after_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
    assert admin_menu_after_save == admin_menu_before_save[::-1]


@pytest.mark.django_db
def test_menu_reset_view(rf, admin_user):
    arrange_url = reverse("shuup_admin:menu.arrange")
    menu_request = apply_request_middleware(rf.get(arrange_url), user=admin_user)
    admin_menu_before_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
    data = {"menus": json.dumps(admin_menu_before_save[::-1])}
    AdminMenuArrangeView.as_view()(apply_request_middleware(rf.post(arrange_url, data=data), user=admin_user))
    admin_menu_after_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
    assert admin_menu_after_save == admin_menu_before_save[::-1]

    reset_url = reverse("shuup_admin:menu.reset")
    request = apply_request_middleware(rf.get(reset_url), user=admin_user)
    response = AdminMenuResetView.as_view()(request)
    assert response.status_code == 302
    admin_menu_after_reset = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
    assert admin_menu_after_reset == admin_menu_before_save


@pytest.mark.django_db
def test_menu_bad_customized_id(rf, admin_user):
    arrange_url = reverse("shuup_admin:menu.arrange")
    menu_request = apply_request_middleware(rf.get(arrange_url), user=admin_user)
    admin_menu_before_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
    bad_entry = admin_menu_before_save[-1]
    bad_entry["id"] = "BAD_ID"
    admin_menu_before_save.append(bad_entry)

    data = {"menus": json.dumps(admin_menu_before_save)}
    AdminMenuArrangeView.as_view()(apply_request_middleware(rf.post(arrange_url, data=data), user=admin_user))

    admin_menu_after_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
    assert len(admin_menu_after_save) == len(admin_menu_before_save) - 1


@pytest.mark.django_db
def test_menu_bad_entry_id(rf, admin_user):
    arrange_url = reverse("shuup_admin:menu.arrange")
    menu_request = apply_request_middleware(rf.get(arrange_url), user=admin_user)
    admin_menu_before_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
    admin_menu_before_save_id = admin_menu_before_save[-1]["id"]
    admin_menu_before_save[-1]["id"] = "BAD_ID"
    admin_menu_before_save[0]["entries"][-1]["id"] = "BAD_ID"

    data = {"menus": json.dumps(admin_menu_before_save)}
    AdminMenuArrangeView.as_view()(apply_request_middleware(rf.post(arrange_url, data=data), user=admin_user))

    admin_menu_after_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
    assert admin_menu_after_save[-1]["id"] != admin_menu_before_save[-1]["id"]
    assert admin_menu_after_save[-1]["id"] == admin_menu_before_save_id


@pytest.mark.django_db
def test_menu_move_child(rf, admin_user):
    arrange_url = reverse("shuup_admin:menu.arrange")
    menu_request = apply_request_middleware(rf.get(arrange_url), user=admin_user)
    admin_menu_before_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]

    # move child on the top level
    entry = admin_menu_before_save[0]["entries"][0]
    del admin_menu_before_save[0]["entries"][0]
    admin_menu_before_save.append(entry)

    data = {"menus": json.dumps(admin_menu_before_save)}
    AdminMenuArrangeView.as_view()(apply_request_middleware(rf.post(arrange_url, data=data), user=admin_user))

    admin_menu_after_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
    assert admin_menu_after_save[-1]["id"] == entry["id"]


@pytest.mark.django_db
def test_menu_flip_parent_child(rf, admin_user):
    arrange_url = reverse("shuup_admin:menu.arrange")
    menu_request = apply_request_middleware(rf.get(arrange_url), user=admin_user)
    admin_menu_before_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]

    # move child on top level and set parent as child
    entry_parent = admin_menu_before_save[0]
    entry = admin_menu_before_save[0]["entries"][0]
    del admin_menu_before_save[0]["entries"][0]
    entry["entries"] = [admin_menu_before_save[0]]
    admin_menu_before_save.append(entry)
    del admin_menu_before_save[0]

    data = {"menus": json.dumps(admin_menu_before_save)}
    AdminMenuArrangeView.as_view()(apply_request_middleware(rf.post(arrange_url, data=data), user=admin_user))

    admin_menu_after_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
    assert admin_menu_after_save[-1]["entries"][0]["id"] == entry_parent["id"]


@pytest.mark.django_db
def test_is_menu_category_active(rf, admin_user):
    url = reverse("shuup_admin:shop_product.list")
    menu_request = apply_request_middleware(rf.get(url), user=admin_user)
    menu_categories = get_menu_entry_categories(menu_request)

    env = Environment()
    context = Context(environment=env, parent=None, name="FauxContext", blocks={})
    context.vars.update({"request": menu_request})

    product_category = [category for category in menu_categories if category.identifier == PRODUCTS_MENU_CATEGORY][0]
    assert is_menu_category_active(context, product_category, menu_request.path)
    assert is_menu_item_active(context, url, menu_request.path)

    shop_category = [category for category in menu_categories if category.identifier == SETTINGS_MENU_CATEGORY][0]
    assert not is_menu_category_active(context, shop_category, menu_request.path)

    with override_settings(SHUUP_ALWAYS_ACTIVE_MENU_CATEGORY_IDENTIFIERS=[SETTINGS_MENU_CATEGORY]):
        assert is_menu_category_active(context, shop_category, menu_request.path)
