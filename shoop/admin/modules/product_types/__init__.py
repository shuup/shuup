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
from shoop.core.models import ProductType


class ProductTypeModule(AdminModule):
    name = _("Product Types")
    breadcrumbs_menu_entry = MenuEntry(name, url="shoop_admin:product-type.list")

    def get_urls(self):
        return [
            admin_url(
                "^product-types/(?P<pk>\d+)/$",
                "shoop.admin.modules.product_types.views.ProductTypeEditView",
                name="product-type.edit"),
            admin_url(
                "^product-types/new/$",
                "shoop.admin.modules.product_types.views.ProductTypeEditView",
                kwargs={"pk": None},
                name="product-type.new"
            ),
            admin_url(
                "^product-types/$",
                "shoop.admin.modules.product_types.views.ProductTypeListView",
                name="product-type.list"
            ),
        ]

    def get_menu_entries(self, request):
        category = _("Products")
        return [
            MenuEntry(
                text=_("Product types"),
                icon="fa fa-asterisk",
                url="shoop_admin:product-type.list",
                category=category
            ),
        ]

    def get_model_url(self, object, kind):
        return derive_model_url(ProductType, "shoop_admin:product-type", object, kind)
