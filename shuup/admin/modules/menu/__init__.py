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


class YourAdminMenuModule(AdminModule):
    name = _("Customize Your Admin Menu")

    def get_urls(self):
        return [
            admin_url(
                r"^menu/your/$",
                "shuup.admin.modules.menu.views.arrange.AdminMenuArrangeView",
                name="menu.arrange"
            ),
            admin_url(
                r"^menu/reset/$",
                "shuup.admin.modules.menu.views.arrange.AdminMenuResetView",
                name="menu.reset"
            )
        ]

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Arrange Your Admin Menu"),
                icon="fa fa-list-alt",
                url="shuup_admin:menu.arrange",
                category=SETTINGS_MENU_CATEGORY,
                ordering=1
            )
        ]


class SuperUserAdminMenuModule(AdminModule):
    name = _("Customize SuperUser Admin Menu")

    def get_urls(self):
        return [
            admin_url(
                r"^menu/superuser/$",
                "shuup.admin.modules.menu.views.arrange.SuperUserMenuArrangeView",
                name="menu.arrange_superuser"
            ),
            admin_url(
                r"^menu/reset/superuser/$",
                "shuup.admin.modules.menu.views.arrange.SuperUserMenuResetView",
                name="menu.reset_superuser"
            )
        ]

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Arrange SuperUser Admin Menu"),
                icon="fa fa-list-alt",
                url="shuup_admin:menu.arrange_superuser",
                category=SETTINGS_MENU_CATEGORY,
                ordering=1
            )
        ]


class StaffAdminMenuModule(AdminModule):
    name = _("Customize Staff Admin Menu")

    def get_urls(self):
        return [
            admin_url(
                r"^menu/staff/$",
                "shuup.admin.modules.menu.views.arrange.StaffMenuArrangeView",
                name="menu.arrange_staff"
            ),
            admin_url(
                r"^menu/reset/staff/$",
                "shuup.admin.modules.menu.views.arrange.StaffMenuResetView",
                name="menu.reset_staff"
            )
        ]

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Arrange Staff Admin Menu"),
                icon="fa fa-list-alt",
                url="shuup_admin:menu.arrange_staff",
                category=SETTINGS_MENU_CATEGORY,
                ordering=1
            )
        ]


class SupplierAdminMenuModule(AdminModule):
    name = _("Customize Supplier Admin Menu")

    def get_urls(self):
        return [
            admin_url(
                r"^menu/supplier/$",
                "shuup.admin.modules.menu.views.arrange.SupplierMenuArrangeView",
                name="menu.arrange_supplier"
            ),
            admin_url(
                r"^menu/reset/supplier/$",
                "shuup.admin.modules.menu.views.arrange.SupplierMenuResetView",
                name="menu.reset_supplier"
            )
        ]

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Arrange Supplier Admin Menu"),
                icon="fa fa-list-alt",
                url="shuup_admin:menu.arrange_supplier",
                category=SETTINGS_MENU_CATEGORY,
                ordering=1
            )
        ]
