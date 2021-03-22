# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry
from shuup.admin.menu import STOREFRONT_MENU_CATEGORY
from shuup.admin.utils.urls import derive_model_url, get_edit_and_list_urls
from shuup.core.models import DisplayUnit, SalesUnit


class SalesUnitModule(AdminModule):
    name = _("Sales Units")
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:sales_unit.list")

    def get_urls(self):
        return get_edit_and_list_urls(
            url_prefix="^sales-units",
            view_template="shuup.admin.modules.sales_units.views.SalesUnit%sView",
            name_template="sales_unit.%s",
        )

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=self.name,
                icon="fa fa-asterisk",
                url="shuup_admin:sales_unit.list",
                category=STOREFRONT_MENU_CATEGORY,
                ordering=5,
            ),
        ]

    def get_model_url(self, object, kind, shop=None):
        return derive_model_url(SalesUnit, "shuup_admin:sales_unit", object, kind)


class DisplayUnitModule(AdminModule):
    name = _("Display Units")
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:display_unit.list")

    def get_urls(self):
        return get_edit_and_list_urls(
            url_prefix="^display-units",
            view_template="shuup.admin.modules.sales_units.views.DisplayUnit%sView",
            name_template="display_unit.%s",
        )

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=self.name,
                icon="fa fa-asterisk",
                url="shuup_admin:display_unit.list",
                category=STOREFRONT_MENU_CATEGORY,
                ordering=5,
            ),
        ]

    def get_model_url(self, object, kind, shop=None):
        return derive_model_url(DisplayUnit, "shuup_admin:display_unit", object, kind)
