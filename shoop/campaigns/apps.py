# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.apps import AppConfig


class CampaignAppConfig(AppConfig):
    name = "shoop.campaigns"
    verbose_name = "Shoop Campaigns"
    label = "campaigns"
    provides = {
        "discount_module": [
            "shoop.campaigns.modules:CatalogCampaignModule"
        ],
        "order_source_modifier_module": [
            "shoop.campaigns.modules:BasketCampaignModule"
        ],
        "admin_module": [
            "shoop.campaigns.admin_module:CampaignAdminModule",
        ],
        "campaign_catalog_filter": [
            "shoop.campaigns.models.catalog_filters:ProductTypeFilter",
            "shoop.campaigns.models.catalog_filters:ProductFilter",
            "shoop.campaigns.models.catalog_filters:CategoryFilter"
        ],
        "campaign_context_condition": [
            "shoop.campaigns.models.context_conditions:ContactGroupCondition",
            "shoop.campaigns.models.context_conditions:ContactCondition",
        ],
        "campaign_basket_condition": [
            "shoop.campaigns.models.basket_conditions:BasketTotalProductAmountCondition",
            "shoop.campaigns.models.basket_conditions:BasketTotalAmountCondition",
            "shoop.campaigns.models.basket_conditions:ProductsInBasketCondition",
            "shoop.campaigns.models.basket_conditions:ContactGroupBasketCondition",
            "shoop.campaigns.models.basket_conditions:ContactBasketCondition",
        ]
    }
