# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.apps import AppConfig


class ShuupTestingAppConfig(AppConfig):
    name = "shuup.testing"
    verbose_name = "Shuup Testing & Demo Utilities"
    label = "shuup_testing"
    provides = {
        "admin_module": [
            "shuup.testing.admin_module:TestingAdminModule"
        ],
        "service_provider_admin_form": [
            "shuup.testing.service_forms:PseudoPaymentProcessorForm",
            "shuup.testing.service_forms:PaymentWithCheckoutPhaseForm",
            "shuup.testing.service_forms:CarrierWithCheckoutPhaseForm",
        ],
        "front_service_checkout_phase_provider": [
            "shuup.testing.simple_checkout_phase.PaymentPhaseProvider",
            "shuup.testing.simple_checkout_phase.ShipmentPhaseProvider",
        ],
        "admin_contact_toolbar_button": [
            "shuup.testing.admin_module.toolbar:MockContactToolbarButton",
        ],
        "admin_contact_edit_toolbar_button": [
            "shuup.testing.admin_module.toolbar:MockContactToolbarButton",
        ],
        "admin_contact_section": [
            "shuup.testing.admin_module.sections:MockContactSection",
        ]
    }


default_app_config = "shuup.testing.ShuupTestingAppConfig"
