# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.signals import Signal

# Modifying signals
get_basket_command_handler = Signal(providing_args=["command"], use_caching=True)
get_method_validation_errors = Signal(providing_args=["method", "source"], use_caching=True)

# Completion signals
order_creator_finished = Signal(providing_args=["order", "source", "request"], use_caching=True)
order_complete_viewed = Signal(providing_args=["order", "request"], use_caching=True)
