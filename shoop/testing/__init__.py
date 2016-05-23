# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.apps import AppConfig


class ShoopTestingAppConfig(AppConfig):
    name = "shoop.testing"
    verbose_name = "Shoop Testing & Demo Utilities"
    label = "shoop_testing"
    provides = {
        "admin_module": [
            "shoop.testing.admin_module:TestingAdminModule"
        ],
        "service_provider_admin_form": [
            "shoop.testing.service_forms:PseudoPaymentProcessorForm",
            "shoop.testing.service_forms:PaymentWithCheckoutPhaseForm",
            "shoop.testing.service_forms:CarrierWithCheckoutPhaseForm",
        ],
        "front_service_checkout_phase_provider": [
            "shoop.testing.simple_checkout_phase.PaymentPhaseProvider",
            "shoop.testing.simple_checkout_phase.ShipmentPhaseProvider",
        ],
    }


default_app_config = "shoop.testing.ShoopTestingAppConfig"
