# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

import shoop.apps


class AppConfig(shoop.apps.AppConfig):
    name = __name__
    verbose_name = _("Simple CMS")
    label = "shoop_simple_cms"

    provides = {
        "front_urls_post": [__name__ + ".urls:urlpatterns"],
        "admin_module": [
            "shoop.simple_cms.admin_module:SimpleCMSAdminModule"
        ],
        "front_template_helper_namespace": [
            "shoop.simple_cms.template_helpers:SimpleCMSTemplateHelpers"
        ]
    }


default_app_config = __name__ + ".AppConfig"
