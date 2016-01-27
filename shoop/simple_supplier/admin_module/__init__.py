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
from shoop.admin.utils.urls import admin_url


class StocksAdminModule(AdminModule):
    name = _("Stock management")
    category = _("Products")

    def get_urls(self):
        return [
            admin_url(
                "^adjust-stock/(?P<supplier_id>\d+)/(?P<product_id>\d+)/",
                "shoop.simple_supplier.admin_module.views.process_stock_adjustment",
                name="simple_supplier.stocks"
            ),
            admin_url(
                "^stocks/",
                "shoop.simple_supplier.admin_module.views.StocksListView",
                name="simple_supplier.stocks"
            ),
        ]

    def get_menu_category_icons(self):
        return {self.name: "fa fa-cubes"}

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=self.name, icon="fa fa-cubes",
                url="shoop_admin:simple_supplier.stocks", category=self.category
            )
        ]
