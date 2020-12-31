# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.dispatch import receiver

from shuup.core.signals import context_cache_item_bumped
from shuup.core.utils import context_cache
from shuup.xtheme.views.plugins import PRODUCT_HIGHLIGHT_CACHE_KEY_PREFIX


@receiver(context_cache_item_bumped, dispatch_uid="xtheme-context-cache-item-bumped")
def handle_context_cache_item_bumped(sender, **kwargs):
    shop_id = kwargs.get("shop_id", None)
    if shop_id:
        cache_key = PRODUCT_HIGHLIGHT_CACHE_KEY_PREFIX % {"shop_id": shop_id}
        context_cache.bump_cache_for_item(cache_key)
