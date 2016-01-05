# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django.utils.translation import ugettext_lazy as _

from .base import BasePaymentMethodModule, BaseShippingMethodModule


class DefaultShippingMethodModule(BaseShippingMethodModule):
    identifier = "default_shipping"
    name = _("Default Shipping")


class DefaultPaymentMethodModule(BasePaymentMethodModule):
    identifier = "default_payment"
    name = _("Default Payment")
