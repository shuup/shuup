# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry
from shuup.admin.menu import SETTINGS_MENU_CATEGORY
from shuup.admin.utils.urls import admin_url


class SettingsModule(AdminModule):
    name = _("System Settings")
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:settings.list")

    def get_urls(self):
        return [
            admin_url(
                "^settings/$",
                "shuup.admin.modules.settings.views.SystemSettingsView",
                name="settings.list"
            )
        ]

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=self.name,
                icon="fa fa-home",
                url="shuup_admin:settings.list",
                category=SETTINGS_MENU_CATEGORY,
                ordering=4
            )
        ]
