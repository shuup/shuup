# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django.db.models.signals import post_save

from shuup.apps import AppConfig
from shuup.campaigns.signal_handlers import update_customers_groups
from shuup.core.models import Payment


class CampaignAppConfig(AppConfig):
    name = "shuup.campaigns"
    verbose_name = "Shuup Campaigns"
    label = "campaigns"
    provides = {
        "admin_contact_group_form_part": [
            "shuup.campaigns.admin_module.form_parts:SalesRangesFormPart"
        ],
        "discount_module": [
            "shuup.campaigns.modules:CatalogCampaignModule"
        ],
        "order_source_modifier_module": [
            "shuup.campaigns.modules:BasketCampaignModule"
        ],
        "admin_module": [
            "shuup.campaigns.admin_module:CampaignAdminModule",
        ],
        "campaign_catalog_filter": [
            "shuup.campaigns.models.catalog_filters:ProductTypeFilter",
            "shuup.campaigns.models.catalog_filters:ProductFilter",
            "shuup.campaigns.models.catalog_filters:CategoryFilter"
        ],
        "campaign_context_condition": [
            "shuup.campaigns.models.context_conditions:ContactGroupCondition",
            "shuup.campaigns.models.context_conditions:ContactCondition",
        ],
        "campaign_basket_condition": [
            "shuup.campaigns.models.basket_conditions:BasketTotalProductAmountCondition",
            "shuup.campaigns.models.basket_conditions:BasketTotalAmountCondition",
            "shuup.campaigns.models.basket_conditions:ProductsInBasketCondition",
            "shuup.campaigns.models.basket_conditions:ContactGroupBasketCondition",
            "shuup.campaigns.models.basket_conditions:ContactBasketCondition",
        ]
    }

    def ready(self):
        post_save.connect(
            update_customers_groups,
            sender=Payment,
            dispatch_uid="contact_group_sales:update_customers_groups")
