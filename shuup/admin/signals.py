# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.dispatch import Signal

object_created = Signal(providing_args=["object"], use_caching=True)
form_post_clean = Signal(
    providing_args=["instance", "cleaned_data"], use_caching=True)
form_pre_clean = Signal(
    providing_args=["instance", "cleaned_data"], use_caching=True)
