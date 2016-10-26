# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum


class ComparisonOperator(Enum):
    EQUALS = 0
    GTE = 1
    LTE = 2

    class Labels:
        EQUALS = _('Exactly')
        GTE = _('Greater than or equal to')
        LTE = _("Lower than or equal to")
