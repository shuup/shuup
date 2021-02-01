# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.dispatch import Signal

view_form_valid = Signal(providing_args=["form", "view", "request"], use_caching=True)
object_created = Signal(providing_args=["object", "request"], use_caching=True)
object_saved = Signal(providing_args=["object", "request"], use_caching=True)
form_post_clean = Signal(
    providing_args=["instance", "cleaned_data"], use_caching=True)
form_pre_clean = Signal(
    providing_args=["instance", "cleaned_data"], use_caching=True)
product_copied = Signal(providing_args=["shop", "copied", "copy"], use_caching=True)
