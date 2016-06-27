# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django.db.models.signals import post_save

from shoop.apps import AppConfig
from shoop.campaigns.signal_handlers import update_customers_groups
from shoop.core.models import Payment


class CampaignAppConfig(AppConfig):
    name = "shoop.campaigns"
    verbose_name = "Shoop Campaigns"
    label = "campaigns"
    provides = {
        "admin_contact_group_form_part": [
            "shoop.campaigns.admin_module.form_parts:SalesRangesFormPart"
        ],
        "discount_module": [
            "shoop.campaigns.modules:CatalogCampaignModule"
        ],
        "order_source_modifier_module": [
            "shoop.campaigns.modules:BasketCampaignModule"
        ],
        "admin_module": [
            "shoop.campaigns.admin_module:CampaignAdminModule",
        ],
        "campaign_basket_condition": [
            "shoop.campaigns.admin_module.forms:BasketTotalProductAmountConditionForm",
            "shoop.campaigns.admin_module.forms:BasketTotalAmountConditionForm",
            "shoop.campaigns.admin_module.forms:BasketMaxTotalProductAmountConditionForm",
            "shoop.campaigns.admin_module.forms:BasketMaxTotalAmountConditionForm",
            "shoop.campaigns.admin_module.forms:ProductsInBasketConditionForm",
            "shoop.campaigns.admin_module.forms:ContactGroupBasketConditionForm",
            "shoop.campaigns.admin_module.forms:ContactBasketConditionForm",
        ],
        "campaign_basket_discount_effect_form": [
            "shoop.campaigns.admin_module.forms:BasketDiscountAmountForm",
            "shoop.campaigns.admin_module.forms:BasketDiscountPercentageForm"
        ],
        "campaign_basket_line_effect_form": [
            "shoop.campaigns.admin_module.forms:FreeProductLineForm",
            "shoop.campaigns.admin_module.forms:DiscountFromProductForm",
        ],
        "campaign_context_condition": [
            "shoop.campaigns.admin_module.forms:ContactGroupConditionForm",
            "shoop.campaigns.admin_module.forms:ContactConditionForm",
        ],
        "campaign_catalog_filter": [
            "shoop.campaigns.admin_module.forms:ProductTypeFilterForm",
            "shoop.campaigns.admin_module.forms:ProductFilterForm",
            "shoop.campaigns.admin_module.forms:CategoryFilterForm"
        ],
        "campaign_product_discount_effect_form": [
            "shoop.campaigns.admin_module.forms:ProductDiscountAmountForm",
            "shoop.campaigns.admin_module.forms:ProductDiscountPercentageForm",
        ],
    }

    def ready(self):
        post_save.connect(
            update_customers_groups,
            sender=Payment,
            dispatch_uid="contact_group_sales:update_customers_groups")
