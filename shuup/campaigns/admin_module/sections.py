# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import Section
from shuup.campaigns.models import BasketCampaign, CatalogCampaign
from shuup.core.models import ShopProduct


class ProductCampaignsSection(Section):
    identifier = "product_campaigns"
    name = _("Active Campaigns")
    icon = "fa-bullhorn"
    template = "shuup/campaigns/admin/_product_campaigns.jinja"

    @classmethod
    def visible_for_object(cls, product, request=None):
        return bool(product.pk)

    @classmethod
    def get_context_data(cls, product, request=None):
        ctx = {}
        shop = request.shop
        try:
            shop_product = product.get_shop_instance(shop)
        except ShopProduct.DoesNotExist:
            return ctx

            ctx[shop] = {
                "basket_campaigns": BasketCampaign.get_for_product(shop_product),
                "catalog_campaigns": CatalogCampaign.get_for_product(shop_product)
            }
        return ctx
