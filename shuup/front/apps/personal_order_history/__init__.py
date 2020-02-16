# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

import shuup.apps


class AppConfig(shuup.apps.AppConfig):
    name = __name__
    verbose_name = _('Shuup Frontend - Personal Order History')
    label = 'shuup_front.personal_order_history'

    provides = {
        'front_urls': [__name__ + '.urls:urlpatterns'],
        'customer_dashboard_items': [
            __name__ + '.dashboard_items:OrderHistoryItem'
        ],
    }


default_app_config = __name__ + '.AppConfig'
