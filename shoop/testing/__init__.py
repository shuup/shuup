# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import shoop.apps


class AppConfig(shoop.apps.AppConfig):
    name = __name__
    verbose_name = "Shoop Testing & Demo Utilities"
    label = "shoop_testing"
    provides = {
        "admin_module": [
            __name__ + ".admin_module:TestingAdminModule"
        ],
        "payment_method_module": [
            __name__ + ".pseudo_payment:PseudoPaymentMethodModule",
        ]
    }


default_app_config = __name__ + ".AppConfig"
