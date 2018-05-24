# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import shuup.apps


class AppConfig(shuup.apps.AppConfig):
    name = "shuup.gdpr"
    label = "shuup_gdpr"
    provides = {
        "admin_module": [
            "shuup.gdpr.admin_module.GDPRModule"
        ],
        "front_urls": [
            "shuup.gdpr.urls:urlpatterns"
        ],
        "xtheme_resource_injection": [
            "shuup.gdpr.resources:add_gdpr_consent_resources"
        ]
    }
