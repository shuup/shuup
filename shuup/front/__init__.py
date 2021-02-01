# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.apps import AppConfig
from shuup.apps.settings import validate_templates_configuration


class ShuupFrontAppConfig(AppConfig):
    name = "shuup.front"
    verbose_name = "Shuup Frontend"
    label = "shuup_front"

    provides = {
        "admin_category_form_part": [
            "shuup.front.admin_module.sorts_and_filters.form_parts.ConfigurationCategoryFormPart"
        ],
        "admin_module": [
            "shuup.front.admin_module.CartAdminModule",
        ],
        "admin_shop_form_part": [
            "shuup.front.admin_module.sorts_and_filters.form_parts.ConfigurationShopFormPart",
            "shuup.front.admin_module.checkout.form_parts.CheckoutShopFormPart",
            "shuup.front.admin_module.companies.form_parts.RegistrationSettingsFormPart",
            "shuup.front.admin_module.translation.form_parts.TranslationSettingsFormPart",
            "shuup.front.admin_module.carts.form_parts.CartDelayFormPart"
        ],
        "notify_event": [
            "shuup.front.notify_events:OrderReceived",
            "shuup.front.notify_events:OrderStatusChanged",
            "shuup.front.notify_events:ShipmentCreated",
            "shuup.front.notify_events:ShipmentDeleted",
            "shuup.front.notify_events:PaymentCreated",
            "shuup.front.notify_events:RefundCreated",
        ],
        "notify_script_template": [
            "shuup.front.notify_script_templates:PaymentCreatedEmailScriptTemplate",
            "shuup.front.notify_script_templates:RefundCreatedEmailScriptTemplate",
            "shuup.front.notify_script_templates:ShipmentDeletedEmailScriptTemplate",
            "shuup.front.notify_script_templates:OrderConfirmationEmailScriptTemplate",
            "shuup.front.notify_script_templates:ShipmentCreatedEmailScriptTemplate",
        ],
        "front_extend_product_list_form": [
            "shuup.front.forms.product_list_modifiers.CategoryProductListFilter",
            "shuup.front.forms.product_list_modifiers.LimitProductListPageSize",
            "shuup.front.forms.product_list_modifiers.ProductPriceFilter",
            "shuup.front.forms.product_list_modifiers.ProductVariationFilter",
            "shuup.front.forms.product_list_modifiers.SortProductListByCreatedDate",
            "shuup.front.forms.product_list_modifiers.SortProductListByAscendingCreatedDate",
            "shuup.front.forms.product_list_modifiers.SortProductListByName",
            "shuup.front.forms.product_list_modifiers.SortProductListByPrice",
            "shuup.front.forms.product_list_modifiers.ManufacturerProductListFilter",
            "shuup.front.forms.product_list_supplier_modifier.SupplierProductListFilter"
        ],
        "front_product_order_form": [
            "shuup.front.forms.order_forms:VariableVariationProductOrderForm",
            "shuup.front.forms.order_forms:SimpleVariationProductOrderForm",
            "shuup.front.forms.order_forms:SimpleProductOrderForm",
        ],
        "front_model_url_resolver": [
            "shuup.front.utils.urls.model_url"
        ]
    }

    def ready(self):
        # connect signals
        import shuup.front.notify_events  # noqa: F401
        import shuup.front.signal_handlers  # noqa: F401
        validate_templates_configuration()


default_app_config = "shuup.front.ShuupFrontAppConfig"
