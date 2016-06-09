# -*- coding: utf-8 -*-

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
