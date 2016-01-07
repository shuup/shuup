# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shoop.admin.base import AdminModule, MenuEntry
from shoop.admin.utils.urls import derive_model_url, get_edit_and_list_urls
from shoop.core.models import Attribute


class AttributeModule(AdminModule):
    name = _("Attributes")
    breadcrumbs_menu_entry = MenuEntry(text=name, url="shoop_admin:attribute.list")

    def get_urls(self):
        return get_edit_and_list_urls(
            url_prefix="^attributes",
            view_template="shoop.admin.modules.attributes.views.Attribute%sView",
            name_template="attribute.%s"
        )

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
