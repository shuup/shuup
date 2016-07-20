# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry
from shuup.admin.menu import CAMPAIGNS_MENU_CATEGORY
from shuup.admin.utils.permissions import (
    get_default_model_permissions, get_permissions_from_urls
)
from shuup.admin.utils.urls import derive_model_url, get_edit_and_list_urls
from shuup.campaigns.models import BasketCampaign, CatalogCampaign, Coupon


class CampaignAdminModule(AdminModule):
    name = _(u"Campaigns")

    def get_urls(self):
        basket_campaign_urls = get_edit_and_list_urls(
            url_prefix="^campaigns/basket",
            view_template="shuup.campaigns.admin_module.views.BasketCampaign%sView",
            name_template="basket_campaigns.%s",
            permissions=get_default_model_permissions(BasketCampaign)
        )

        coupon_urls = get_edit_and_list_urls(
            url_prefix="^campaigns/coupons",
            view_template="shuup.campaigns.admin_module.views.Coupon%sView",
            name_template="coupons.%s",
            permissions=get_default_model_permissions(Coupon)
        )

        return basket_campaign_urls + coupon_urls + get_edit_and_list_urls(
            url_prefix="^campaigns/catalog",
            view_template="shuup.campaigns.admin_module.views.CatalogCampaign%sView",
            name_template="catalog_campaigns.%s",
            permissions=get_default_model_permissions(CatalogCampaign)
        )

    def get_menu_category_icons(self):
        return {self.name: "fa fa-bullhorn"}

    def get_menu_entries(self, request):
        category = CAMPAIGNS_MENU_CATEGORY
        return [
            MenuEntry(
                text=_("Catalog Campaigns"), icon="fa fa-file-text",
                url="shuup_admin:catalog_campaigns.list",
                category=category, ordering=1, aliases=[_("Show Catalog Campaigns")]
            ),
            MenuEntry(
                text=_("Basket Campaigns"), icon="fa fa-file-text",
                url="shuup_admin:basket_campaigns.list",
                category=category, ordering=2, aliases=[_("Show Basket Campaigns")]
            ),
            MenuEntry(
                text=_("Coupons"), icon="fa fa-file-text",
                url="shuup_admin:coupons.list",
                category=category, ordering=3, aliases=[_("Show Coupons")]
            )
        ]

    def get_required_permissions(self):
        return get_permissions_from_urls(self.get_urls())

    def get_model_url(self, object, kind):
        if not hasattr(object, "admin_url_suffix"):
            return super(CampaignAdminModule, self).get_model_url(object, kind)
        admin_url = "shuup_admin:%s" % object.admin_url_suffix
        return derive_model_url(type(object), admin_url, object, kind)
