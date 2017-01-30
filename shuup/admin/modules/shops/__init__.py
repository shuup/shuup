# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
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
from shuup.admin.views.home import SimpleHelpBlock
from shuup.core.models import Shop


class ShopModule(AdminModule):
    name = _("Shops")
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:shop.list")

    def get_urls(self):
        return [
            admin_url(
                "^shops/(?P<pk>\d+)/enable/$",
                "shuup.admin.modules.shops.views.ShopEnablerView",
                name="shop.enable",
                permissions=["shuup.change_shop"]
            ),
        ] + get_edit_and_list_urls(
            url_prefix="^shops",
            view_template="shuup.admin.modules.shops.views.Shop%sView",
            name_template="shop.%s",
            model=Shop
        )

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=self.name,
                icon="fa fa-house",
                url="shuup_admin:shop.list",
                category=STOREFRONT_MENU_CATEGORY,
                subcategory="settings",
                ordering=4
            ),
        ]

    def get_help_blocks(self, request, kind):
        if kind == "setup":
            shop = request.session.get("admin_shop")
            yield SimpleHelpBlock(
                text=_("Add a logo to make your store stand out"),
                actions=[{
                    "text": _("Add logo"),
                    "url": self.get_model_url(shop, "edit"),
                    "hash": "#shop-images-section"
                }],
                icon_url="shuup_admin/img/logo-icon.svg",
                done=shop.logo
            )

    def get_required_permissions(self):
        return ["shuup.view_shop"]

    def get_model_url(self, object, kind):
        return derive_model_url(Shop, "shuup_admin:shop", object, kind)
