# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.configuration import get as original_configuration_get
from shuup.core.setting_keys import SHUUP_PRICING_MODULE


def get_customer_group_pricing_patched_configuration(shop, key, default=None):
    if key == SHUUP_PRICING_MODULE:
        return "customer_group_pricing"
    return original_configuration_get(shop, key, default)
