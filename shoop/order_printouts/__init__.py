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
    verbose_name = _("Order printouts")
    label = "shoop_order_printouts"

    provides = {
        "admin_module": [
            "shoop.order_printouts.admin_module:PrintoutsAdminModule"
        ],
        "admin_order_toolbar_button": [
            "shoop.order_printouts.admin_module.toolbar:SimplePrintoutsToolbarButton"
        ],
    }

default_app_config = __name__ + ".AppConfig"
