# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from shoop.admin.forms import ShoopAdminForm
from shoop.core.models import CustomCarrier, CustomPaymentProcessor


class CustomCarrierForm(ShoopAdminForm):
    class Meta:
        model = CustomCarrier
        exclude = ("identifier", )


class CustomPaymentProcessorForm(ShoopAdminForm):
    class Meta:
        model = CustomPaymentProcessor
        exclude = ("identifier", )
