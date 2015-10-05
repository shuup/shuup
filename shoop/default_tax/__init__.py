# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _

import shoop.apps


class AppConfig(shoop.apps.AppConfig):
    name = __name__
    verbose_name = _("Shoop Default Tax")
    label = "default_tax"

    provides = {
        "tax_module": ["shoop.default_tax.module:DefaultTaxModule"],
        "admin_module": ["shoop.default_tax.admin_module:TaxRulesAdminModule"],
    }


default_app_config = __name__ + ".AppConfig"
