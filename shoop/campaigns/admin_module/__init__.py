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


class CampaignAdminModule(AdminModule):
    name = _(u"Campaigns")

    def get_urls(self):
        basket_campaign_urls = get_edit_and_list_urls(
            url_prefix="^campaigns/basket",
            view_template="shoop.campaigns.admin_module.views.BasketCampaign%sView",
            name_template="basket_campaigns.%s"
        )

        coupon_urls = get_edit_and_list_urls(
            url_prefix="^campaigns/coupons",
            view_template="shoop.campaigns.admin_module.views.Coupon%sView",
            name_template="coupons.%s"
        )

        return basket_campaign_urls + coupon_urls + get_edit_and_list_urls(
            url_prefix="^campaigns/catalog",
            view_template="shoop.campaigns.admin_module.views.CatalogCampaign%sView",
            name_template="catalog_campaigns.%s"
        )

    def get_menu_category_icons(self):
        return {self.name: "fa fa-bullhorn"}

    def get_menu_entries(self, request):
        category = self.name
        return [
            MenuEntry(
                text=_("Catalog Campaigns"), icon="fa fa-file-text",
                url="shoop_admin:catalog_campaigns.list",
                category=category, aliases=[_("Show Catalog Campaigns")]
            ),
            MenuEntry(
                text=_("Basket Campaigns"), icon="fa fa-file-text",
                url="shoop_admin:basket_campaigns.list",
                category=category, aliases=[_("Show Basket Campaigns")]
            ),
            MenuEntry(
                text=_("Coupons"), icon="fa fa-file-text",
                url="shoop_admin:coupons.list",
                category=category, aliases=[_("Show Coupons")]
            )
        ]

    def get_model_url(self, object, kind):
        if not hasattr(object, "admin_url_suffix"):
            return super(CampaignAdminModule, self).get_model_url(object, kind)
        admin_url = "shoop_admin:%s" % object.admin_url_suffix
        return derive_model_url(type(object), admin_url, object, kind)
