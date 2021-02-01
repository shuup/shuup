# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry
from shuup.admin.menu import CONTENT_MENU_CATEGORY
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
            admin_url(
                r"^media/folder/(?P<pk>\d+)/$",
                "shuup.admin.modules.media.views.MediaFolderEditView",
                name="media.edit-access"
            ),
            admin_url(
                "^media/upload/$",
                "shuup.admin.modules.media.views.media_upload",
                name="media.upload"
            )
        ]

    def get_extra_permissions(self):
        permissions = super().get_extra_permissions()
        permissions += (
            # Allows the users to view all folders, not limited to the once that they have access to.
            "media.view-all",

            # Allows the user to create a folder anywhere, not limited to folders under their root folder.
            "media.create-folder",

            # Allows the user to rename all folders, not limited to folders under their root folder.
            "media.rename-folder",

            # Allows the user to delete all folders, not limited to folders under their root folder.
            "media.delete-folder",

            # Allows the user to upload content to all folders, not limited to folders under their root folder.
            "media.upload-to-folder",

            # Allows the user to rename all files, not limeted to files that the user has uploaded.
            "media.rename-file",

            # Allows the user to delete all files, not limeted to files that the user has uploaded.
            "media.delete-file",
        )
        return permissions

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Media browser"),
                icon="fa fa-folder-open",
                url="shuup_admin:media.browse",
                category=CONTENT_MENU_CATEGORY,
                ordering=2
            ),
        ]
