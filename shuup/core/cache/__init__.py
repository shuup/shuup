# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
"""
Utilities for versioned caching and automatic timeout determination.

Versioning works by way of namespaces. Namespaces are the first
colon-separated part of cache keys.

For instance, the cache keys ``price:10``, ``price:20``, and ``price``
all belong to the ``price`` namespace and can be invalidated with
one ``bump_version("price")`` call.

The versions themselves are stored within the cache, within the
``_version`` namespace.  (As an implementation detail, this allows one
to invalidate _all_ versioned keys by bumping the version of
``_version``. Very meta!)
"""

from .impl import VersionedCache

__all__ = [
    "bump_version",
    "clear",
    "get",
    "set",
    "VersionedCache",
]

_default_cache = None
get = None
set = None
bump_version = None
clear = None


def init_cache():
    global _default_cache, get, set, bump_version, clear
    _default_cache = VersionedCache(using="default")
    get = _default_cache.get
    set = _default_cache.set
    bump_version = _default_cache.bump_version
    clear = _default_cache.clear


init_cache()
