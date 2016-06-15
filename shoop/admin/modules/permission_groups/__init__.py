# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib.auth.models import Group as PermissionGroup
from django.utils.translation import ugettext_lazy as _

from shoop.admin.base import AdminModule, MenuEntry
from shoop.admin.utils.urls import derive_model_url, get_edit_and_list_urls


class PermissionGroupModule(AdminModule):
    name = _("Permission Groups")
    category = _("Permission Groups")
    breadcrumbs_menu_entry = MenuEntry(name, url="shoop_admin:permission_groups.list")

    def get_urls(self):
        return get_edit_and_list_urls(
            url_prefix="^permission-groups",
            view_template="shoop.admin.modules.permission_groups.views.PermissionGroup%sView",
            name_template="permission_groups.%s"
        )

    def get_menu_category_icons(self):
        return {self.category: "fa fa-users"}

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=self.name,
                icon="fa fa-users",
                url="shoop_admin:permission_groups.list",
                category=_("Contacts")
            )
        ]

    def get_model_url(self, object, kind):
        return derive_model_url(PermissionGroup, "shoop_admin:permission_groups", object, kind)
