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


class AdminMenuModule(AdminModule):
    """
    Module that customizes dashboard admin menu
    """
    name = _("Admin menu")
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:admin_menu.arrange")

    def get_urls(self):
        return [
            admin_url(
                r"^admin_menu/$",
                "shuup.admin.modules.admin_menu.views.AdminMenuArrangeView",
                name="admin_menu.arrange"
            ),
            admin_url(
                r"^admin_menu/reset/$",
                "shuup.admin.modules.admin_menu.views.AdminMenuResetView",
                name="admin_menu.reset"
            ),
        ]

    def get_menu_entries(self, request):
        category = SETTINGS_MENU_CATEGORY
        return [
            MenuEntry(
                text=_("Admin menu"),
                icon="fa fa-list-alt",
                url="shuup_admin:admin_menu.arrange",
                category=category,
                subcategory="admin_menu",
                ordering=1
            ),
        ]
