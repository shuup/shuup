# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry
from shuup.admin.menu import CONTENT_MENU_CATEGORY
from shuup.admin.utils.urls import admin_url


class ProductFilterModule(AdminModule):
    name = _("Product filter")
    breadcrumbs_menu_entry = MenuEntry(name,
                                       url="shuup_admin:product_filter.list")

    def get_urls(self):
        return [
            admin_url(
                "^product_filter/$",
                "shuup.front.apps.product_filter.views.ProductFilterSettingsView",
                name="product_filter.list",
            ),
        ]

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=self.name,
                icon="fa fa-house",
                url="shuup_admin:product_filter.list",
                category=CONTENT_MENU_CATEGORY,
                subcategory="elements",
                ordering=3
            ),
        ]
