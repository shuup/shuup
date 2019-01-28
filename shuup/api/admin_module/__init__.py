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
from shuup.admin.utils.urls import admin_url


class APIModule(AdminModule):
    name = _("API")

    def get_urls(self):
        return [
            admin_url(
                "^system/api/$",
                "shuup.api.admin_module.views.permissions.APIPermissionView",
                name="api_permission"
            )
        ]

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("API"),
                icon="fa fa-code",
                url="shuup_admin:api_permission",
                category=SETTINGS_MENU_CATEGORY,
                subcategory="permissions",
            )
        ]
