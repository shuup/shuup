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
from shuup.admin.modules.menu.views.arrange import SuperUserMenuArrangeView, SuperUserMenuResetView
from shuup.admin.template_helpers.shuup_admin import is_menu_category_active, is_menu_item_active
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import reverse


def test_menu_arrange_view(rf, admin_user):
    url = reverse("shuup_admin:menu.arrange_superuser")
    request = apply_request_middleware(rf.get(url), user=admin_user)
    response = SuperUserMenuArrangeView.as_view()(request)
    assert response.status_code == 200


@pytest.mark.django_db
def test_menu_save_arrange_view(rf, admin_user):
    url = reverse("shuup_admin:menu.arrange_superuser")

    menu_request = apply_request_middleware(rf.get(url), user=admin_user)
    admin_menu_before_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
    data = {"menus": json.dumps(admin_menu_before_save[::-1])}
    request = apply_request_middleware(rf.post(url, data=data), user=admin_user)
    response = SuperUserMenuArrangeView.as_view()(request)
    assert response.status_code == 302

    menu_request = apply_request_middleware(rf.get(url), user=admin_user)
    admin_menu_after_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
    assert admin_menu_after_save == admin_menu_before_save[::-1]


@pytest.mark.django_db
def test_menu_reset_view(rf, admin_user):
    arrange_url = reverse("shuup_admin:menu.arrange_superuser")
    menu_request = apply_request_middleware(rf.get(arrange_url), user=admin_user)
    admin_menu_before_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
    data = {"menus": json.dumps(admin_menu_before_save[::-1])}
    SuperUserMenuArrangeView.as_view()(apply_request_middleware(rf.post(arrange_url, data=data), user=admin_user))
    admin_menu_after_save = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
    assert admin_menu_after_save == admin_menu_before_save[::-1]

    reset_url = reverse("shuup_admin:menu.reset_superuser")
    request = apply_request_middleware(rf.get(reset_url), user=admin_user)
    response = SuperUserMenuResetView.as_view()(request)
    assert response.status_code == 302
    admin_menu_after_reset = [m.to_dict() for m in get_menu_entry_categories(menu_request)]
    assert admin_menu_after_reset == admin_menu_before_save
