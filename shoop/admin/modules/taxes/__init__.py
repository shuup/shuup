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
from shoop.core.models.taxes import Tax, TaxClass, CustomerTaxGroup


class TaxModule(AdminModule):
    name = _("Taxes")
    category = name
    breadcrumbs_menu_entry = MenuEntry(name, url="shoop_admin:tax_class.list")

    def get_urls(self):
        return [

            # TODO: Add url for tax dashboard?

            # urls for Tax
            admin_url(
                "^taxes/tax/(?P<pk>\d+)/$",
                "shoop.admin.modules.taxes.views.edit.TaxEditView",
                name="tax.edit"
            ),
            admin_url(
                "^taxes/tax/new/$",
                "shoop.admin.modules.taxes.views.edit.TaxEditView",
                kwargs={"pk": None},
                name="tax.new"
            ),
            admin_url(
                "^taxes/tax/$",
                "shoop.admin.modules.taxes.views.list.TaxListView",
                name="tax.list"
            ),

            # urls for CustomerTaxGroup
            admin_url(
                "^taxes/customer-tax-group/(?P<pk>\d+)/$",
                "shoop.admin.modules.taxes.views.edit.CustomerTaxGroupEditView",
                name="customer_tax_group.edit"
            ),
            admin_url(
                "^taxes/customer-tax-group/new/$",
                "shoop.admin.modules.taxes.views.edit.CustomerTaxGroupEditView",
                kwargs={"pk": None},
                name="customer_tax_group.new"),
            admin_url(
                "^taxes/customer-tax-group/$",
                "shoop.admin.modules.taxes.views.list.CustomerTaxGroupListView",
                name="customer_tax_group.list"
            ),

            # urls for TaxClass
            admin_url(
                "^taxes/tax-class/(?P<pk>\d+)/$",
                "shoop.admin.modules.taxes.views.edit.TaxClassEditView",
                name="tax_class.edit"
            ),
            admin_url(
                "^taxes/tax-class/new/$",
                "shoop.admin.modules.taxes.views.edit.TaxClassEditView",
                kwargs={"pk": None},
                name="tax_class.new"
            ),
            admin_url(
                "^taxes/tax-class/$",
                "shoop.admin.modules.taxes.views.list.TaxClassListView",
                name="tax_class.list"
            ),
        ]

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
