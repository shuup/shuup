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
from shoop.core.models import SalesUnit


class SalesUnitModule(AdminModule):
    name = _("Sales Units")
    breadcrumbs_menu_entry = MenuEntry(name, url="shoop_admin:sales-unit.list")

    def get_urls(self):
        return get_edit_and_list_urls(
            url_prefix="^sales-units",
            view_template="shoop.admin.modules.sales_units.views.SalesUnit%sView",
            name_template="sales-unit.%s"
        )

    def get_menu_entries(self, request):
        category = _("Products")
        return [
            MenuEntry(
                text=self.name,
                icon="fa fa-asterisk",
                url="shoop_admin:sales-unit.list",
                category=category
            ),
        ]

    def get_model_url(self, object, kind):
        return derive_model_url(SalesUnit, "shoop_admin:sales-unit", object, kind)
