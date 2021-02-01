# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.apps import AppConfig


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
        "admin_product_section": [
            "shuup.campaigns.admin_module.sections:ProductCampaignsSection"
        ],
        "campaign_basket_condition": [
            "shuup.campaigns.admin_module.forms:BasketTotalProductAmountConditionForm",
            "shuup.campaigns.admin_module.forms:BasketTotalAmountConditionForm",
            "shuup.campaigns.admin_module.forms:BasketTotalUndiscountedProductAmountConditionForm",
            "shuup.campaigns.admin_module.forms:BasketMaxTotalProductAmountConditionForm",
            "shuup.campaigns.admin_module.forms:BasketMaxTotalAmountConditionForm",
            "shuup.campaigns.admin_module.forms:ProductsInBasketConditionForm",
            "shuup.campaigns.admin_module.forms:ContactGroupBasketConditionForm",
            "shuup.campaigns.admin_module.forms:ContactBasketConditionForm",
            "shuup.campaigns.admin_module.forms:CategoryProductsBasketConditionForm",
            "shuup.campaigns.admin_module.forms:HourBasketConditionForm",
            "shuup.campaigns.admin_module.forms:ChildrenProductConditionForm",
        ],
        "campaign_basket_discount_effect_form": [
            "shuup.campaigns.admin_module.forms:BasketDiscountAmountForm",
            "shuup.campaigns.admin_module.forms:BasketDiscountPercentageForm",
            "shuup.campaigns.admin_module.forms:DiscountPercentageFromUndiscountedForm",
        ],
        "campaign_basket_line_effect_form": [
            "shuup.campaigns.admin_module.forms:FreeProductLineForm",
            "shuup.campaigns.admin_module.forms:DiscountFromProductForm",
            "shuup.campaigns.admin_module.forms:DiscountFromCategoryProductsForm",
        ],
        "campaign_context_condition": [
            "shuup.campaigns.admin_module.forms:ContactGroupConditionForm",
            "shuup.campaigns.admin_module.forms:ContactConditionForm",
            "shuup.campaigns.admin_module.forms:HourConditionForm",
        ],
        "campaign_catalog_filter": [
            "shuup.campaigns.admin_module.forms:ProductTypeFilterForm",
            "shuup.campaigns.admin_module.forms:ProductFilterForm",
            "shuup.campaigns.admin_module.forms:CategoryFilterForm"
        ],
        "campaign_product_discount_effect_form": [
            "shuup.campaigns.admin_module.forms:ProductDiscountAmountForm",
            "shuup.campaigns.admin_module.forms:ProductDiscountPercentageForm",
        ],
        "reports": [
            "shuup.campaigns.reports:CouponsUsageReport"
        ]
    }

    def ready(self):
        from django.db.models.signals import m2m_changed, post_save
        from shuup.campaigns.models import CategoryFilter, ProductFilter, ProductTypeFilter
        from shuup.campaigns.models import ContactCondition, ContactGroupCondition
        from shuup.campaigns.signal_handlers import (
            invalidate_context_condition_cache,
            update_customers_groups, update_filter_cache
        )
        from shuup.core.models import ContactGroup, Payment, ShopProduct
        post_save.connect(
            update_customers_groups,
            sender=Payment,
            dispatch_uid="contact_group_sales:update_customers_groups"
        )

        # Invalidate context condition caches
        m2m_changed.connect(
            invalidate_context_condition_cache,
            sender=ContactGroup.members.through,
            dispatch_uid="campaigns:invalidate_caches_for_contact_group_m2m_change"
        )
        m2m_changed.connect(
            invalidate_context_condition_cache,
            sender=ContactCondition.contacts.through,
            dispatch_uid="campaigns:invalidate_caches_for_contacts_condition_m2m_change"
        )
        m2m_changed.connect(
            invalidate_context_condition_cache,
            sender=ContactGroupCondition.contact_groups.through,
            dispatch_uid="campaigns:invalidate_caches_for_contact_group_condition_m2m_change"
        )

        # Invalidate context filter caches
        m2m_changed.connect(
            update_filter_cache,
            sender=CategoryFilter.categories.through,
            dispatch_uid="campaigns:invalidate_caches_for_category_filter_m2m_change"
        )
        m2m_changed.connect(
            update_filter_cache,
            sender=ProductFilter.products.through,
            dispatch_uid="campaigns:invalidate_caches_for_product_filter_m2m_change"
        )
        m2m_changed.connect(
            update_filter_cache,
            sender=ProductTypeFilter.product_types.through,
            dispatch_uid="campaigns:invalidate_caches_for_product_type_filter_m2m_change"
        )
        post_save.connect(
            update_filter_cache,
            sender=ShopProduct,
            dispatch_uid="campaigns:invalidate_caches_for_shop_product_save"
        )
        m2m_changed.connect(
            update_filter_cache,
            sender=ShopProduct.categories.through,
            dispatch_uid="campaigns:invalidate_caches_for_shop_product_m2m_change"
        )
