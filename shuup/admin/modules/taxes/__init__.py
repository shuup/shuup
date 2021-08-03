# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from typing import Iterable

from shuup.admin.base import AdminModule, MenuEntry
from shuup.admin.menu import SETTINGS_MENU_CATEGORY
from shuup.admin.utils.object_selector import get_object_selector_permission_name
from shuup.admin.utils.urls import derive_model_url, get_edit_and_list_urls
from shuup.core.models import CustomerTaxGroup, Tax, TaxClass


class TaxModule(AdminModule):
    name = _("Taxes")

    def get_urls(self):
        # TODO: Add url for tax dashboard?
        tax_urls = get_edit_and_list_urls(
            url_prefix="^taxes/tax", view_template="shuup.admin.modules.taxes.views.Tax%sView", name_template="tax.%s"
        )
        tax_group_urls = get_edit_and_list_urls(
            url_prefix="^taxes/customer-tax-group",
            view_template="shuup.admin.modules.taxes.views.CustomerTaxGroup%sView",
            name_template="customer_tax_group.%s",
        )
        tax_class_urls = get_edit_and_list_urls(
            url_prefix="^taxes/tax-class",
            view_template="shuup.admin.modules.taxes.views.TaxClass%sView",
            name_template="tax_class.%s",
        )
        return tax_urls + tax_group_urls + tax_class_urls

    def get_menu_entries(self, request):
        category = SETTINGS_MENU_CATEGORY
        return [
            MenuEntry(
                text=_("Taxes"), icon="fa fa-pie-chart", url="shuup_admin:tax.list", category=category, ordering=1
            ),
            MenuEntry(
                text=_("Customer Tax Groups"),
                icon="fa fa-pie-chart",
                url="shuup_admin:customer_tax_group.list",
                category=category,
                ordering=2,
            ),
            MenuEntry(
                text=_("Tax Classes"),
                icon="fa fa-pie-chart",
                url="shuup_admin:tax_class.list",
                category=category,
                ordering=3,
            ),
        ]

    def get_model_url(self, object, kind, shop=None):
        return (
            derive_model_url(Tax, "shuup_admin:tax", object, kind)
            or derive_model_url(TaxClass, "shuup_admin:tax_class", object, kind)
            or derive_model_url(CustomerTaxGroup, "shuup_admin:customer_tax_group", object, kind)
        )

    def get_extra_permissions(self) -> Iterable[str]:
        return [
            get_object_selector_permission_name(CustomerTaxGroup),
            get_object_selector_permission_name(Tax),
            get_object_selector_permission_name(TaxClass),
        ]

    def get_permissions_help_texts(self) -> Iterable[str]:
        return {
            get_object_selector_permission_name(CustomerTaxGroup): _(
                "Allow the user to select customer tax groups in admin."
            ),
            get_object_selector_permission_name(Tax): _("Allow the user to select taxes in admin."),
            get_object_selector_permission_name(TaxClass): _("Allow the user to select tax classes in admin."),
        }
