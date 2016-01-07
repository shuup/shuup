# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _

import shoop.apps


class ShoopUtilsAppConfig(shoop.apps.AppConfig):
    name = __name__
    verbose_name = _("Shoop Utilities")
    label = "shoop_utils"


default_app_config = __name__ + ".ShoopUtilsAppConfig"

# There's a small elephant in this file.

#       ,
#      ((_,-.
#       '-.\_)'-,
#          )  _ )'-   PjP
# ,.;.,;,,(/(/ \));,;.,.,
