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
from shuup.admin.utils.urls import admin_url


class StocksAdminModule(AdminModule):
    name = _("Stock management")

    def get_urls(self):
        return [
            admin_url(
                "^adjust-stock/(?P<supplier_id>\d+)/(?P<product_id>\d+)/",
                "shuup.simple_supplier.admin_module.views.process_stock_adjustment",
                name="simple_supplier.stocks"
            ),
            admin_url(
                "^alert-limit/(?P<supplier_id>\d+)/(?P<product_id>\d+)/",
                "shuup.simple_supplier.admin_module.views.process_alert_limit",
                name="simple_supplier.alert_limits"
            ),
            admin_url(
                "^manage-stock/(?P<supplier_id>\d+)/(?P<product_id>\d+)/",
                "shuup.simple_supplier.admin_module.views.process_stock_managed",
                name="simple_supplier.stock_managed"
            ),
            admin_url(
                "^stocks/",
                "shuup.simple_supplier.admin_module.views.StocksListView",
                name="simple_supplier.stocks"
            ),
            admin_url(
                "^list-settings/",
                "shuup.admin.modules.settings.views.ListSettingsView",
                name="simple_supplier.list_settings"
            )
        ]

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=self.name,
                icon="fa fa-cubes",
                url="shuup_admin:simple_supplier.stocks",
                category=STOREFRONT_MENU_CATEGORY,
                ordering=6
            )
        ]
