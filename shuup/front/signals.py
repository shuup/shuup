# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.signals import Signal

# Modifying signals
get_basket_command_handler = Signal(providing_args=["command"], use_caching=True)

# Completion signals
order_complete_viewed = Signal(providing_args=["order", "request"], use_caching=True)
