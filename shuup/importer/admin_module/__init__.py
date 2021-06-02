# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry
from shuup.admin.menu import SETTINGS_MENU_CATEGORY
from shuup.admin.utils.urls import admin_url
from shuup.apps.provides import get_provide_objects


class ImportAdminModule(AdminModule):
    name = _("Data Import")
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:importer.import")

    def get_extra_permissions(self):
        extra_permissions = ["importer.show-all-imports"]
        importers_permissions = [importer.get_permission_identifier() for importer in get_provide_objects("importers")]
        return extra_permissions + importers_permissions

    def get_permissions_help_texts(self):
        help_texts = {
            "importer.show-all-imports": _("Allow the user to see the imports from all shops and suppliers."),
            "importer.import_process": _("Allow the user to run importers."),
            "importer.import": _("Allow the user to list imports."),
            "importer.import.new": _("Allow the user to import a file."),
            "importer.download_example": _("Allow the user to download sample files."),
        }

        for importer in get_provide_objects("importers"):
            help_texts[importer.get_permission_identifier()] = _(
                "Allow the user to use the {importer_name} importer."
            ).format(importer_name=importer.name)

        return help_texts

    def get_urls(self):
        return [
            admin_url(
                "^importer/imports/$", "shuup.importer.admin_module.import_views.ImportListView", name="importer.import"
            ),
            admin_url(
                r"^importer/imports/(?P<pk>.+)/$",
                "shuup.importer.admin_module.import_views.ImportDetailView",
                name="importer.import.detail",
            ),
            admin_url(
                "^importer/new/$",
                "shuup.importer.admin_module.import_views.ImportView",
                name="importer.import.new",
            ),
            admin_url(
                "^importer/process$",
                "shuup.importer.admin_module.import_views.ImportProcessView",
                name="importer.import_process",
            ),
            admin_url(
                "^importer/example$",
                "shuup.importer.admin_module.import_views.ExampleFileDownloadView",
                name="importer.download_example",
            ),
        ]

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Data Import"),
                category=SETTINGS_MENU_CATEGORY,
                url="shuup_admin:importer.import",
                icon="fa fa-star",
            )
        ]
