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
from shuup.core.models import Supplier


class SupplierModule(AdminModule):
    name = _("Suppliers")
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:supplier.list")

    def get_urls(self):
        return get_edit_and_list_urls(
            url_prefix="^suppliers",
            view_template="shuup.admin.modules.suppliers.views.Supplier%sView",
            name_template="supplier.%s"
        ) + [admin_url(
            r"^suppliers/delete/(?P<pk>\d+)/$",
            "shuup.admin.modules.suppliers.views.SupplierDeleteView",
            name="supplier.delete",
            permissions=("supplier.delete",)
        ), ]

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Suppliers"),
                icon="fa fa-truck",
                url="shuup_admin:supplier.list",
                category=STOREFRONT_MENU_CATEGORY,
                ordering=7
            ),
        ]

    def get_model_url(self, object, kind, shop=None):
        return derive_model_url(Supplier, "shuup_admin:supplier", object, kind)
