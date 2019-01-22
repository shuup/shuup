# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import shuup.apps


class AppConfig(shuup.apps.AppConfig):
    name = "shuup.discounts"
    provides = {
        "admin_module": [
            "shuup.discounts.admin.modules.DiscountModule",
            "shuup.discounts.admin.modules.AvailabilityExceptionModule",
            "shuup.discounts.admin.modules.HappyHourModule",
            "shuup.discounts.admin.modules.CouponCodeModule",
        ],
        "discount_module": ["shuup.discounts.modules:ProductDiscountModule"],
        "order_source_modifier_module": ["shuup.discounts.modules:CouponCodeModule"],
        "xtheme_plugin": [
            "shuup.discounts.plugins:DiscountedProductsPlugin"
        ]
    }

    def ready(self):
        import shuup.discounts.signal_handers   # noqa F401
