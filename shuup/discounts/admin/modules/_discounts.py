# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry
from shuup.admin.menu import CAMPAIGNS_MENU_CATEGORY
from shuup.admin.utils.permissions import get_default_model_permissions
from shuup.admin.utils.urls import derive_model_url, get_edit_and_list_urls
from shuup.discounts.models import Discount


class DiscountModule(AdminModule):
    name = _("Discounts")
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:discounts.list")

    def get_urls(self):
        from shuup.admin.urls import admin_url
        archive = admin_url(
            "^archived_discounts",
            "shuup.discounts.admin.views.ArchivedDiscountListView",
            name="discounts.archive",
            permissions=get_default_model_permissions(Discount)
        )

        delete = admin_url(
            "^discounts/(?P<pk>\d+)/delete/$",
            "shuup.discounts.admin.views.DiscountDeleteView",
            name="discounts.delete",
            permissions=get_default_model_permissions(Discount)
        )

        return [archive, delete] + get_edit_and_list_urls(
            url_prefix="^discounts",
            view_template="shuup.discounts.admin.views.Discount%sView",
            name_template="discounts.%s",
            permissions=get_default_model_permissions(Discount)
        )

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Product Discounts"),
                icon="fa fa-percentage",
                url="shuup_admin:discounts.list",
                category=CAMPAIGNS_MENU_CATEGORY,
                ordering=4
            ),
            MenuEntry(
                text=_("Archived Product Discounts"),
                icon="fa fa-percentage",
                url="shuup_admin:discounts.archive",
                category=CAMPAIGNS_MENU_CATEGORY,
                ordering=5
            )
        ]

    def get_required_permissions(self):
        return get_default_model_permissions(Discount)

    def get_model_url(self, object, kind, shop=None):
        return derive_model_url(Discount, "shuup_admin:discounts", object, kind)
