# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _
from shoop.admin.base import AdminModule, MenuEntry
from shoop.admin.utils.urls import derive_model_url, get_edit_and_list_urls
from shoop.core.models import Tax, TaxClass, CustomerTaxGroup


class TaxModule(AdminModule):
    name = _("Taxes")
    category = name
    breadcrumbs_menu_entry = MenuEntry(name, url="shoop_admin:tax_class.list")

    def get_urls(self):
        # TODO: Add url for tax dashboard?
        tax_urls = get_edit_and_list_urls(
            url_prefix="^taxes/tax",
            view_template="shoop.admin.modules.taxes.views.Tax%sView",
            name_template="tax.%s"
        )
        tax_group_urls = get_edit_and_list_urls(
            url_prefix="^taxes/customer-tax-group",
            view_template="shoop.admin.modules.taxes.views.CustomerTaxGroup%sView",
            name_template="customer_tax_group.%s"
        )
        tax_class_urls = get_edit_and_list_urls(
            url_prefix="^taxes/tax-class",
            view_template="shoop.admin.modules.taxes.views.TaxClass%sView",
            name_template="tax_class.%s"
        )
        return tax_urls + tax_group_urls + tax_class_urls

    def get_menu_category_icons(self):
        return {self.category: "fa fa-pie-chart"}

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("List Taxes"), icon="fa fa-list", url="shoop_admin:tax.list",
                category=self.category
            ),
            MenuEntry(
                text=_("List Customer Tax Groups"), icon="fa fa-list", url="shoop_admin:customer_tax_group.list",
                category=self.category
            ),
            MenuEntry(
                text=_("List Tax Classes"), icon="fa fa-list", url="shoop_admin:tax_class.list",
                category=self.category
            )
        ]

    def get_model_url(self, object, kind):
        return (
            derive_model_url(Tax, "shoop_admin:tax", object, kind) or
            derive_model_url(TaxClass, "shoop_admin:tax_class", object, kind) or
            derive_model_url(CustomerTaxGroup, "shoop_admin:customer_tax_group", object, kind)
        )
