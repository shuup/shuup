# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.apps import AppConfig


class DiscountPricingAppConfig(AppConfig):
    name = "shoop.discount_pricing"
    verbose_name = "Shoop Discount Pricing"
    label = "discount_pricing"
    provides = {
        "pricing_module": [
            "shoop.discount_pricing.module:DiscountPricingModule"
        ],
        "admin_product_form_part": [
            "shoop.discount_pricing.admin_form_part:DiscountPricingFormPart"
        ],
    }


default_app_config = "shoop.discount_pricing.DiscountPricingAppConfig"
