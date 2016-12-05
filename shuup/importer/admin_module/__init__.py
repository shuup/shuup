# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry
from shuup.admin.menu import SETTINGS_MENU_CATEGORY
from shuup.admin.utils.permissions import get_default_model_permissions
from shuup.admin.utils.urls import admin_url
from shuup.core.models import Shop


class ImportAdminModule(AdminModule):
    name = _("Data Import")
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:importer.import")

    def get_urls(self):
        return [
            admin_url(
                "^importer/import$",
                "shuup.importer.admin_module.import_views.ImportView",
                name="importer.import",
                permissions=get_default_model_permissions(Shop)
            ),
            admin_url(
                "^importer/import/process$",
                "shuup.importer.admin_module.import_views.ImportProcessView",
                name="importer.import_process",
                permissions=get_default_model_permissions(Shop)
            ),
        ]

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Data Import"),
                category=SETTINGS_MENU_CATEGORY,
                subcategory="data_transfer",
                url="shuup_admin:importer.import",
                icon="fa fa-star"
            )
        ]
