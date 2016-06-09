# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry
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
                "^media/$",
                "shuup.admin.modules.media.views.MediaBrowserView",
                name="media.browse"
            ),
        ]

    def get_menu_category_icons(self):
        return {self.name: "fa fa-image"}

    def get_menu_entries(self, request):
        category = _("Media")
        return [
            MenuEntry(
                text=_("Media browser"),
                icon="fa fa-folder-open",
                url="shuup_admin:media.browse",
                category=category
            ),
        ]
