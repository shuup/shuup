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
from shuup.admin.utils.urls import derive_model_url, get_edit_and_list_urls
from shuup.discounts.models import CouponCode


class CouponCodeModule(AdminModule):
    name = _("Product Discounts Coupon Codes")
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:discounts_coupon_codes.list")

    def get_urls(self):
        from shuup.admin.urls import admin_url
        delete = admin_url(
            "^discounts_coupon_codes/(?P<pk>\d+)/delete/$",
            "shuup.discounts.admin.views.CouponCodeDeleteView",
            name="discounts_coupon_codes.delete"
        )

        return [delete] + get_edit_and_list_urls(
            url_prefix="^discounts_coupon_codes",
            view_template="shuup.discounts.admin.views.CouponCode%sView",
            name_template="discounts_coupon_codes.%s"
        )

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Product Discounts Coupon Codes"),
                icon="fa fa-percent",
                url="shuup_admin:discounts_coupon_codes.list",
                category=CAMPAIGNS_MENU_CATEGORY,
                ordering=8
            )
        ]

    def get_model_url(self, object, kind, shop=None):
        return derive_model_url(CouponCode, "shuup_admin:discounts_coupon_codes", object, kind)
