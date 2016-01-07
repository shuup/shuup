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
from shoop.default_tax.models import TaxRule


class TaxRulesAdminModule(AdminModule):
    name = _("Tax Rules")
    category = _("Taxes")
    breadcrumbs_menu_entry = MenuEntry(name, "shoop_admin:default_tax.tax_rule.list")

    def get_urls(self):
        return get_edit_and_list_urls(
            url_prefix="^default-tax/rules",
            view_template="shoop.default_tax.admin_module.views.TaxRule%sView",
            name_template="default_tax.tax_rule.%s"
        )

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Tax Rules"), icon="fa fa-file-text",
                url="shoop_admin:default_tax.tax_rule.list",
                category=self.category, aliases=[_("Show tax rules")]
            )
        ]

    def get_model_url(self, object, kind):
        return derive_model_url(TaxRule, "shoop_admin:default_tax.tax_rule", object, kind)
