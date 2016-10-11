# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import django.conf

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
            "shuup.front.forms.product_list_modifiers.SortProductListByCreatedDate",
            "shuup.front.forms.product_list_modifiers.SortProductListByName",
            "shuup.front.forms.product_list_modifiers.SortProductListByPrice",
            "shuup.front.forms.product_list_modifiers.ManufacturerProductListFilter",
        ],
    }

    def ready(self):
        # connect signals
        import shuup.front.notify_events  # noqa: F401

        validate_templates_configuration()
        if django.conf.settings.SHUUP_FRONT_INSTALL_ERROR_HANDLERS:
            from .error_handling import install_error_handlers
            install_error_handlers()


default_app_config = "shuup.front.ShuupFrontAppConfig"
