# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _

import shoop.apps


# TODO: Document how to create custom pricing modules (Refs SHOOP-514)
class CustomerGroupPricingAppConfig(shoop.apps.AppConfig):
    name = __name__
    verbose_name = _("Shoop Customer Group Pricing")
    label = "shoop_customer_group_pricing"
    provides = {
        "pricing_module": [
            __name__ + ".module:CustomerGroupPricingModule"
        ],
        "admin_product_form_part": [
            __name__ + ".admin_form_part:CustomerGroupPricingFormPart"
        ],
        "api_populator": [
            __name__ + ".api:populate_customer_group_pricing_api"
        ]
    }


default_app_config = __name__ + ".CustomerGroupPricingAppConfig"
