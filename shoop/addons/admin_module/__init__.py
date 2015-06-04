# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.admin.base import AdminModule, MenuEntry
from django.utils.translation import ugettext_lazy as _
from shoop.admin.utils.urls import admin_url


class AddonModule(AdminModule):
    name = _("Addons")
    category = name
    breadcrumbs_menu_entry = MenuEntry(text=name, url="shoop_admin:addon.list")

    def get_urls(self):
        return [
            admin_url(
                "^addons/$",
                "shoop.addons.admin_module.views.AddonListView",
                name="addon.list"
            ),
            admin_url(
                "^addons/add/$",
                "shoop.addons.admin_module.views.AddonUploadView",
                name="addon.upload"
            ),
            admin_url(
                "^addons/add/confirm/$",
                "shoop.addons.admin_module.views.AddonUploadConfirmView",
                name="addon.upload_confirm"
            ),
            admin_url(
                "^addons/reload/$",
                "shoop.addons.admin_module.views.ReloadView",
                name="addon.reload"
            ),
        ]

    def get_menu_category_icons(self):
        return {self.category: "fa fa-puzzle-piece"}

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Addons"),
                icon="fa fa-puzzle-piece",
                url="shoop_admin:addon.list",
                category=self.category
            )
        ]
