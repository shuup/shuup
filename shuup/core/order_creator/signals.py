# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.signals import Signal

post_compute_source_lines = Signal(
    providing_args=["source", "lines"], use_caching=True)
order_creator_finished = Signal(
    providing_args=["order", "source"], use_caching=True)
post_order_line_save = Signal(
    providing_args=["order_line", "order"], use_caching=True)
