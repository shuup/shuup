# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry, SearchResult
from shuup.admin.menu import STOREFRONT_MENU_CATEGORY
from shuup.admin.shop_provider import get_shop
from shuup.admin.utils.urls import admin_url, derive_model_url, get_edit_and_list_urls, get_model_url
from shuup.admin.views.home import SimpleHelpBlock
from shuup.core.models import Shop, ShopStatus
from shuup.utils.django_compat import reverse


class ShopModule(AdminModule):
    name = _("Shops")
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:shop.list")

    def get_urls(self):
        return [
            admin_url(
                r"^shops/(?P<pk>\d+)/enable/$", "shuup.admin.modules.shops.views.ShopEnablerView", name="shop.enable"
            ),
            admin_url(
                r"^shops/(?P<pk>\d+)/select/$", "shuup.admin.modules.shops.views.ShopSelectView", name="shop.select"
            ),
        ] + get_edit_and_list_urls(
            url_prefix="^shops", view_template="shuup.admin.modules.shops.views.Shop%sView", name_template="shop.%s"
        )

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=self.name,
                icon="fa fa-home",
                url="shuup_admin:shop.list",
                category=STOREFRONT_MENU_CATEGORY,
                ordering=4,
            ),
        ]

    def get_help_blocks(self, request, kind):
        if kind == "setup":
            shop = request.shop
            yield SimpleHelpBlock(
                text=_("Add a logo to make your store stand out"),
                actions=[
                    {"text": _("Add logo"), "url": self.get_model_url(shop, "edit"), "hash": "#shop-images-section"}
                ],
                icon_url="shuup_admin/img/logo_icon.svg",
                done=shop.logo,
                required=False,
            )

            shop = get_shop(request)
            yield SimpleHelpBlock(
                priority=1000,
                text=_("Publish your store"),
                description=_("Let customers browse your store and make purchases"),
                css_class="green ",
                actions=[
                    {
                        "method": "POST",
                        "text": _("Publish shop"),
                        "url": reverse("shuup_admin:shop.enable", kwargs={"pk": shop.pk}),
                        "data": {"enable": True, "redirect": reverse("shuup_admin:dashboard")},
                    }
                ],
                icon_url="shuup_admin/img/publish.png",
                done=(not shop.maintenance_mode),
                required=False,
            )

    def get_model_url(self, object, kind, shop=None):
        return derive_model_url(Shop, "shuup_admin:shop", object, kind)

    def get_search_results(self, request, query):
        if not settings.SHUUP_ENABLE_MULTIPLE_SHOPS:
            return

        minimum_query_length = 3
        if len(query) >= minimum_query_length:
            shops = Shop.objects.get_for_user(request.user).filter(
                translations__name__icontains=query, status=ShopStatus.ENABLED
            )
            for i, shop in enumerate(shops[:10]):
                relevance = 100 - i
                yield SearchResult(
                    text=(_('Set "{}" as the active shop')).format(shop.name),
                    url=get_model_url(shop, "select"),
                    category=(_("Available Shops [currently active: {}]")).format(request.shop.name),
                    relevance=relevance,
                )
