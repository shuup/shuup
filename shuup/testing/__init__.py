# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.apps import AppConfig


def activate_sqlite_fk_constraint(sender, connection, **kwargs):
    """Enable integrity constraint with SQLite and not running browser tests."""
    import os
    if connection.vendor == 'sqlite' and os.environ.get("SHUUP_BROWSER_TESTS") != "1":
        cursor = connection.cursor()
        cursor.execute('PRAGMA foreign_keys = ON;')


class ShuupTestingAppConfig(AppConfig):
    name = "shuup.testing"
    verbose_name = "Shuup Testing & Demo Utilities"
    label = "shuup_testing"
    provides = {
        "admin_module": [
            "shuup.testing.modules.mocker:TestingAdminModule",
            "shuup.testing.modules.sample_data:SampleDataAdminModule",
            "shuup.testing.modules.demo:DemoModule",
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
            "shuup.testing.modules.mocker.toolbar:MockContactToolbarButton",
        ],
        "admin_contact_toolbar_action_item": [
             "shuup.testing.modules.mocker.toolbar:MockContactToolbarActionItem",
        ],
        "admin_contact_edit_toolbar_button": [
            "shuup.testing.modules.mocker.toolbar:MockContactToolbarButton",
        ],
        "admin_shop_edit_toolbar_button": [
            "shuup.testing.modules.mocker.toolbar:MockShopToolbarButton",
        ],
        "admin_product_toolbar_action_item": [
            "shuup.testing.modules.mocker.toolbar:MockProductToolbarActionItem",
        ],
        "admin_contact_section": [
            "shuup.testing.modules.mocker.sections:MockContactSection",
        ],
        "importers": [
            "shuup.testing.importers.DummyImporter",
            "shuup.testing.importers.DummyFileImporter"
        ],
        "xtheme": [
            __name__ + ".themes:ShuupTestingTheme",
            __name__ + ".themes:ShuupTestingThemeWithCustomBase",
        ],
        "pricing_module": [
            "shuup.testing.supplier_pricing.pricing:SupplierPricingModule"
        ],
    }

    def ready(self):
        from django.db.backends.signals import connection_created
        connection_created.connect(activate_sqlite_fk_constraint)


default_app_config = "shuup.testing.ShuupTestingAppConfig"
