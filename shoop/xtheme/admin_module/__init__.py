# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _
from shoop.admin.base import AdminModule, MenuEntry
from shoop.admin.utils.urls import admin_url


class XthemeAdminModule(AdminModule):
    name = _("Shoop Extensible Theme Engine")
    category = _("System")
    breadcrumbs_menu_entry = MenuEntry(_("Theme Configuration"), "shoop_admin:xtheme.config")

    def get_urls(self):
        return [
            admin_url(
                "^xtheme/(?P<theme_identifier>.+?)/",
                "shoop.xtheme.admin_module.views.ThemeConfigDetailView",
                name="xtheme.config_detail"
            ),
            admin_url(
                "^xtheme/",
                "shoop.xtheme.admin_module.views.ThemeConfigView",
                name="xtheme.config"
            )
        ]

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Theme Configuration"), icon="fa fa-paint-brush",
                url="shoop_admin:xtheme.config",
                category=self.category
            )
        ]
