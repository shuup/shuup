# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shoop.admin.base import AdminModule, MenuEntry
from shoop.admin.utils.urls import (
    admin_url, derive_model_url, get_edit_and_list_urls
)
from shoop.social_media.models import SocialMediaLink


class SocialMediaAdminModule(AdminModule):
    name = _("Social Media")
    breadcrumbs_menu_entry = MenuEntry(text=name, url="shoop_admin:social_media_link.list")

    def get_urls(self):
        return get_edit_and_list_urls(
            url_prefix="^social_media_links",
            view_template="shoop.social_media.admin_module.views.SocialMediaLink%sView",
            name_template="social_media_link.%s"
        ) + [
            admin_url(
                "^social_media_links/(?P<pk>\d+)/delete/$",
                "shoop.social_media.admin_module.views.SocialMediaLinkDeleteView",
                name="social_media_link.delete"
            ),
        ]

    def get_menu_category_icons(self):
        return {self.name: "fa fa-plus-square"}

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Social Media Links"),
                icon="fa fa-link",
                url="shoop_admin:social_media_link.list",
                category=_("Social Media")
            )
        ]

    def get_model_url(self, object, kind):
        return derive_model_url(SocialMediaLink, "shoop_admin:social_media_link", object, kind)
