# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from shuup.admin.base import AdminModule, MenuEntry
from shuup.admin.menu import SETTINGS_MENU_CATEGORY
from shuup.admin.utils.urls import admin_url


class TestingAdminModule(AdminModule):
    def get_urls(self):
        return [
            admin_url(
                "^mocker/$",
                "shuup.testing.modules.mocker.mocker_view.MockerView",
                name="mocker"
            )
        ]

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text="Create Mock Objects",
                category=SETTINGS_MENU_CATEGORY,
                subcategory="data_transfer",
                url="shuup_admin:mocker",
                icon="fa fa-star"
            )
        ]
