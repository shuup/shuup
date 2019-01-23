# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry
from shuup.admin.menu import SETTINGS_MENU_CATEGORY
from shuup.admin.utils.permissions import AdminCustomModelPermissionDef
from shuup.admin.utils.urls import admin_url
from shuup.core.models import Shop


class TestingAdminModule(AdminModule):
    name = _("Testing")

    def get_urls(self):
        return [
            admin_url(
                "^mocker/$",
                "shuup.testing.admin_module.mocker_view.MockerView",
                name="mocker",
                permissions=[AdminCustomModelPermissionDef(Shop, "create_mock_data", _("Can create mock data"))]
            )
        ]

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Create Mock Objects"),
                category=SETTINGS_MENU_CATEGORY,
                subcategory="data_transfer",
                url="shuup_admin:mocker",
                icon="fa fa-star"
            )
        ]
