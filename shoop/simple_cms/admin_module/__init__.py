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
from shoop.admin.utils.urls import admin_url, derive_model_url
from shoop.simple_cms.models import Page


class SimpleCMSAdminModule(AdminModule):
    name = _(u"Simple CMS")
    breadcrumbs_menu_entry = MenuEntry(name, "shoop_admin:simple_cms.page.list")

    def get_urls(self):
        return [
            admin_url(
                "cms/page/(?P<pk>\d+)/",
                "shoop.simple_cms.admin_module.views.PageEditView",
                name="simple_cms.page.edit"
            ),
            admin_url(
                "cms/page/new/",
                "shoop.simple_cms.admin_module.views.PageEditView",
                kwargs={"pk": None},
                name="simple_cms.page.new"
            ),
            admin_url(
                "cms/pages/",
                "shoop.simple_cms.admin_module.views.PageListView",
                name="simple_cms.page.list"
            ),
        ]

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
