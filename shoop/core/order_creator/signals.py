# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.signals import Signal

post_compute_source_lines = Signal(
    providing_args=["source", "lines"], use_caching=True)
