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
from shuup.admin.menu import CAMPAIGNS_MENU_CATEGORY
from shuup.admin.urls import admin_url
from shuup.admin.utils.urls import derive_model_url, get_edit_and_list_urls
from shuup.discounts.models import Discount


class DiscountModule(AdminModule):
    name = _("Discounts")

    def get_urls(self):
        return get_edit_and_list_urls(
            url_prefix="^discounts",
            view_template="shuup.discounts.admin.views.Discount%sView",
            name_template="discounts.%s"
        )

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Product Discounts"),
                icon="fa fa-percent",
                url="shuup_admin:discounts.list",
                category=CAMPAIGNS_MENU_CATEGORY,
                ordering=4
            ),
        ]

    def get_model_url(self, object, kind, shop=None):
        return derive_model_url(Discount, "shuup_admin:discounts", object, kind)


class DiscountArchiveModule(AdminModule):
    name = _("Archived Product Discounts")
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:discounts.archive")

    def get_urls(self):
        return [
            admin_url(
                "^archived_discounts",
                "shuup.discounts.admin.views.ArchivedDiscountListView",
                name="discounts.archive"
            ),
            admin_url(
                r"^discounts/(?P<pk>\d+)/delete/$",
                "shuup.discounts.admin.views.DiscountDeleteView",
                name="discounts.delete"
            )
        ]

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Archived Product Discounts"),
                icon="fa fa-percent",
                url="shuup_admin:discounts.archive",
                category=CAMPAIGNS_MENU_CATEGORY,
                ordering=5
            )
        ]
