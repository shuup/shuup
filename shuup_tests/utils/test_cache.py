# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.test import override_settings

from shuup.core import cache


def test_cache_api():
    with override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "test_configuration_cache",
            }
        }
    ):
        cache.init_cache()

        key = "test_prefix:123"
        value = "456"
        cache.set(key, value)
        assert cache.get(key) == value
        cache.bump_version(key)
        assert cache.get(key, default="derp") == "derp"  # version was bumped, so no way this is there
        cache.set(key, value)
        assert cache.get(key) == value
