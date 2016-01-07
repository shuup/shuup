# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.apps import AppConfig


# TODO: Document how to create custom pricing modules (Refs SHOOP-514)
class ShoopSimplePricingAppConfig(AppConfig):
    name = "shoop.simple_pricing"
    verbose_name = "Shoop Simple Pricing"
    label = "simple_pricing"
    provides = {
        "pricing_module": [
            "shoop.simple_pricing.module:SimplePricingModule"
        ],
        "admin_product_form_part": [
            "shoop.simple_pricing.admin_form_part:SimplePricingFormPart"
        ],
        "api_populator": [
            "shoop.simple_pricing.api:populate_simple_pricing_api"
        ]
    }


default_app_config = "shoop.simple_pricing.ShoopSimplePricingAppConfig"
