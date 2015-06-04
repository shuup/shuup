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
from shoop.core.models import Attribute


class AttributeModule(AdminModule):
    name = _("Attributes")
    breadcrumbs_menu_entry = MenuEntry(text=name, url="shoop_admin:attribute.list")

    def get_urls(self):
        return [
            admin_url(
                "^attributes/(?P<pk>\d+)/$",
                "shoop.admin.modules.attributes.views.AttributeEditView",
                name="attribute.edit"),
            admin_url(
                "^attributes/new/$",
                "shoop.admin.modules.attributes.views.AttributeEditView",
                kwargs={"pk": None},
                name="attribute.new"
            ),
            admin_url(
                "^attributes/$",
                "shoop.admin.modules.attributes.views.AttributeListView",
                name="attribute.list"
            ),
        ]

    def get_menu_category_icons(self):
        return {self.name: "fa fa-tags"}

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Attributes"),
                icon="fa fa-tags",
                url="shoop_admin:attribute.list",
                category=self.name
            )
        ]

    def get_model_url(self, object, kind):
        return derive_model_url(Attribute, "shoop_admin:attribute", object, kind)
