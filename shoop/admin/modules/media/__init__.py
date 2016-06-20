# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _
from filer.models import File

from shoop.admin.base import AdminModule, MenuEntry
from shoop.admin.utils.permissions import get_default_model_permissions
from shoop.admin.utils.urls import admin_url


class MediaModule(AdminModule):
    """
    A module for handling site media.
    Basically a frontend for the Django-Filer app.
    """

    name = _("Media")

    def get_urls(self):
        return [
            admin_url(
                "^media/$",
                "shoop.admin.modules.media.views.MediaBrowserView",
                name="media.browse",
                permissions=get_default_model_permissions(File),
            ),
        ]

    def get_menu_category_icons(self):
        return {self.name: "fa fa-image"}

    def get_required_permissions(self):
        return get_default_model_permissions(File)

    def get_menu_entries(self, request):
        category = _("Media")
        return [
            MenuEntry(
                text=_("Media browser"),
                icon="fa fa-folder-open",
                url="shoop_admin:media.browse",
                category=category
            ),
        ]
