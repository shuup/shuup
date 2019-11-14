# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry
from shuup.admin.menu import CAMPAIGNS_MENU_CATEGORY
from shuup.admin.utils.urls import derive_model_url, get_edit_and_list_urls
from shuup.admin.views.home import HelpBlockCategory, SimpleHelpBlock
from shuup.campaigns.admin_module.utils import (
    get_extra_permissions_for_admin_module
)
from shuup.campaigns.models import BasketCampaign, Coupon


class CampaignAdminModule(AdminModule):
    name = _(u"Campaigns")

    def get_urls(self):
        basket_campaign_urls = get_edit_and_list_urls(
            url_prefix="^campaigns/basket",
            view_template="shuup.campaigns.admin_module.views.BasketCampaign%sView",
            name_template="basket_campaign.%s"
        )

        coupon_urls = get_edit_and_list_urls(
            url_prefix="^campaigns/coupons",
            view_template="shuup.campaigns.admin_module.views.Coupon%sView",
            name_template="coupon.%s"
        )

        catalog_campaign_urls = get_edit_and_list_urls(
            url_prefix="^campaigns/catalog",
            view_template="shuup.campaigns.admin_module.views.CatalogCampaign%sView",
            name_template="catalog_campaign.%s"
        ) if _show_catalog_campaigns_in_admin() else []

        return basket_campaign_urls + catalog_campaign_urls + coupon_urls

    def get_menu_category_icons(self):
        return {self.name: "fa fa-bullhorn"}

    def get_menu_entries(self, request):
        category = CAMPAIGNS_MENU_CATEGORY
        menu_entries = [
            MenuEntry(
                text=_("Basket Campaigns"), icon="fa fa-file-text",
                url="shuup_admin:basket_campaign.list",
                category=category, ordering=2, aliases=[_("Show Basket Campaigns")]
            ),
            MenuEntry(
                text=_("Coupons"), icon="fa fa-file-text",
                url="shuup_admin:coupon.list",
                category=category, ordering=3, aliases=[_("Show Coupons")]
            )
        ]

        if _show_catalog_campaigns_in_admin():
            menu_entries.append(
                MenuEntry(
                    text=_("Catalog Campaigns"), icon="fa fa-file-text",
                    url="shuup_admin:catalog_campaign.list",
                    category=category, ordering=1, aliases=[_("Show Catalog Campaigns")]
                )
            )

        return menu_entries

    def get_help_blocks(self, request, kind):
        if kind == "quicklink":
            yield SimpleHelpBlock(
                text=_("Set up a sales campaign"),
                actions=[{
                    "text": _("New basket campaign"),
                    "url": self.get_model_url(BasketCampaign, "new")
                }, {
                    "text": _("New coupon"),
                    "url": self.get_model_url(Coupon, "new")
                }],
                priority=1,
                category=HelpBlockCategory.CAMPAIGNS,
                icon_url="shuup/campaigns/img/campaign.png"
            )

    def get_model_url(self, object, kind, shop=None):
        if not hasattr(object, "admin_url_suffix"):
            return super(CampaignAdminModule, self).get_model_url(object, kind)
        admin_url = "shuup_admin:%s" % object.admin_url_suffix
        return derive_model_url(type(object), admin_url, object, kind)

    def get_extra_permissions(self):
        return get_extra_permissions_for_admin_module()


def _show_catalog_campaigns_in_admin():
    return bool("catalog_campaigns" in settings.SHUUP_DISCOUNT_MODULES)
