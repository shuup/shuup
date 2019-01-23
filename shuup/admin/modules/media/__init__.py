# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _
from filer.models import File

from shuup.admin.base import AdminModule, MenuEntry
from shuup.admin.menu import CONTENT_MENU_CATEGORY
from shuup.admin.utils.permissions import AdminDefaultModelPermissionDef
from shuup.admin.utils.urls import admin_url


class MediaModule(AdminModule):
    """
    A module for handling site media.
    Basically a frontend for the Django-Filer app.
    """

    name = _("Media")

    def get_urls(self):
        return [
            admin_url(
                r"^media/$",
                "shuup.admin.modules.media.views.MediaBrowserView",
                name="media.browse",
                permissions=[
                    AdminDefaultModelPermissionDef(File, "change"),
                    AdminDefaultModelPermissionDef(File, "add"),
                    AdminDefaultModelPermissionDef(File, "delete")
                ]
            ),
        ]

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Media browser"),
                icon="fa fa-folder-open",
                url="shuup_admin:media.browse",
                category=CONTENT_MENU_CATEGORY,
                subcategory="other",
                ordering=2
            ),
        ]
