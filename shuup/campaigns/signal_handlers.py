# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.campaigns.consts import (
    CAMPAIGNS_CACHE_NAMESPACE, CATALOG_FILTER_CACHE_NAMESPACE,
    CONTEXT_CONDITION_CACHE_NAMESPACE
)
from shuup.core import cache


def invalidate_context_condition_cache(sender, instance, **kwargs):
    cache.bump_version(CAMPAIGNS_CACHE_NAMESPACE)
    cache.bump_version(CONTEXT_CONDITION_CACHE_NAMESPACE)


def invalidate_context_filter_cache(sender, instance, **kwargs):
    cache.bump_version(CAMPAIGNS_CACHE_NAMESPACE)
    # Let's try to preserve catalog filter cache as long as possible
    cache.bump_version("%s:%s" % (CATALOG_FILTER_CACHE_NAMESPACE, instance.pk))
