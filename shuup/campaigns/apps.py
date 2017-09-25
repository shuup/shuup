# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.apps import AppConfig


class CampaignAppConfig(AppConfig):
    name = "shuup.campaigns"
    verbose_name = "Shuup Campaigns"
    label = "campaigns"
    provides = {
        "discount_module": [
            "shuup.campaigns.modules:CatalogCampaignModule"
        ],
        "order_source_modifier_module": [
            "shuup.campaigns.modules:BasketCampaignModule"
        ],
        "admin_module": [
            "shuup.campaigns.admin_module:CampaignAdminModule",
        ],
        "admin_product_section": [
            "shuup.campaigns.admin_module.sections:ProductCampaignsSection"
        ],
        "campaign_basket_condition": [],
        "campaign_basket_discount_effect_form": [],
        "campaign_basket_line_effect_form": [],
        "campaign_context_condition": [],
        "campaign_catalog_filter": [],
        "campaign_product_discount_effect_form": []
    }

    def ready(self):
        from django.db.models.signals import m2m_changed
        from shuup.campaigns.signal_handlers import invalidate_context_condition_cache
        from shuup.core.models import ContactGroup
        # Invalidate context condition caches
        m2m_changed.connect(
            invalidate_context_condition_cache,
            sender=ContactGroup.members.through,
            dispatch_uid="campaigns:invalidate_caches_for_contact_group_m2m_change"
        )
