# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
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
            "shuup.front.admin_module.sorts_and_filters.form_parts.ConfigurationShopFormPart"
        ],
        "notify_event": [
            "shuup.front.notify_events:OrderReceived",
            "shuup.front.notify_events:ShipmentCreated",
            "shuup.front.notify_events:ShipmentDeleted",
            "shuup.front.notify_events:PaymentCreated",
            "shuup.front.notify_events:RefundCreated",
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
        ],
        "api_populator": [
            "shuup.front.api:populate_front_api"
        ],
    }

    def ready(self):
        # connect signals
        import shuup.front.notify_events  # noqa: F401

        validate_templates_configuration()


default_app_config = "shuup.front.ShuupFrontAppConfig"
