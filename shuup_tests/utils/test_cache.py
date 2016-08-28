# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from shuup.core import cache


def test_cache_api():
    key = "test_prefix:123"
    value = "456"
    cache.set(key, value)
    assert cache.get(key) == value
    cache.bump_version(key)
    assert cache.get(key, default="derp") == "derp"  # version was bumped, so no way this is there
    cache.set(key, value)
    assert cache.get(key) == value
