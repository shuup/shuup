# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import shuup.apps


class AppConfig(shuup.apps.AppConfig):
    name = "shuup.gdpr"
    label = "shuup_gdpr"
    provides = {
        "admin_module": ["shuup.gdpr.admin_module.GDPRModule"],
        "front_urls": ["shuup.gdpr.urls:urlpatterns"],
        "customer_dashboard_items": ["shuup.gdpr.dashboard_items:GDPRDashboardItem"],
        "admin_contact_toolbar_action_item": [
            "shuup.gdpr.admin_module.toolbar:AnonymizeContactToolbarButton",
            "shuup.gdpr.admin_module.toolbar:DownloadDataToolbarButton",
        ],
        "xtheme_resource_injection": ["shuup.gdpr.resources:add_gdpr_consent_resources"],
        "front_registration_field_provider": ["shuup.gdpr.providers:GDPRRegistrationFieldProvider"],
        "front_auth_form_field_provider": ["shuup.gdpr.providers:GDPRAuthFieldProvider"],
        "checkout_confirm_form_field_provider": ["shuup.gdpr.providers:GDPRCheckoutFieldProvider"],
        "front_company_registration_form_provider": ["shuup.gdpr.providers:GDPRFormDefProvider"],
    }

    def ready(self):
        # connect receivers
        import shuup.gdpr.receivers  # noqa: F401
        import shuup.gdpr.signal_handlers  # noqa: F401
