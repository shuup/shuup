# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry
from shuup.admin.menu import STOREFRONT_MENU_CATEGORY
from shuup.admin.utils.urls import (
    admin_url, derive_model_url, get_edit_and_list_urls
)
from shuup.core.models import Attribute


class AttributeModule(AdminModule):
    name = _("Attributes")
    breadcrumbs_menu_entry = MenuEntry(text=name, url="shuup_admin:attribute.list")

    def get_urls(self):
        return [
            admin_url(
                r"^attributes/(?P<pk>\d+)/delete/$",
                "shuup.admin.modules.attributes.views.edit.AttributeDeleteView",
                name="attribute.delete"
            )
        ] + get_edit_and_list_urls(
            url_prefix="^attributes",
            view_template="shuup.admin.modules.attributes.views.Attribute%sView",
            name_template="attribute.%s"
        )

    def get_menu_category_icons(self):
        return {self.name: "fa fa-tags"}

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Attributes"),
                icon="fa fa-tags",
                url="shuup_admin:attribute.list",
                category=STOREFRONT_MENU_CATEGORY,
                ordering=8
            )
        ]

    def get_model_url(self, object, kind, shop=None):
        return derive_model_url(Attribute, "shuup_admin:attribute", object, kind)
