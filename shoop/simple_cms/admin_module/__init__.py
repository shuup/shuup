# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from shoop.admin.base import AdminModule, MenuEntry
from django.utils.translation import ugettext_lazy as _
from shoop.admin.utils.urls import derive_model_url, get_edit_and_list_urls
from shoop.simple_cms.models import Page


class SimpleCMSAdminModule(AdminModule):
    name = _(u"Simple CMS")
    breadcrumbs_menu_entry = MenuEntry(name, "shoop_admin:simple_cms.page.list")

    def get_urls(self):
        return get_edit_and_list_urls(
            url_prefix="^cms/page",
            view_template="shoop.simple_cms.admin_module.views.Page%sView",
            name_template="simple_cms.page.%s"
        )

    def get_menu_category_icons(self):
        return {self.name: "fa fa-pencil-square-o"}

    def get_menu_entries(self, request):
        category = _("Simple CMS")
        return [
            MenuEntry(
                text=_("Pages"), icon="fa fa-file-text",
                url="shoop_admin:simple_cms.page.list",
                category=category, aliases=[_("Show pages")]
            )
        ]

    def get_model_url(self, object, kind):
        return derive_model_url(Page, "shoop_admin:simple_cms.page", object, kind)
