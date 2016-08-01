# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

import shuup.apps


class AppConfig(shuup.apps.AppConfig):
    name = __name__
    verbose_name = _('Shuup Frontend - Saved Baskets')
    label = 'shuup_front.saved_baskets'

    provides = {
        'front_urls': [__name__ + '.urls:urlpatterns'],
    }


default_app_config = __name__ + '.AppConfig'
