# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import logging
import random
import threading
import time
from pickle import PicklingError

from django.conf import settings
from django.core.cache import caches
from django.core.signals import request_finished
from django.utils.encoding import force_str

DEFAULT_CACHE_DURATIONS = {
    # Add default durations for various namespaces here (in seconds)
}

LOGGER = logging.getLogger(__name__)

_versions = threading.local()


def _clear_versions_for_request(**kwargs):
    _versions.__dict__.clear()


request_finished.connect(_clear_versions_for_request, dispatch_uid="shuup.core.cache._clear_versions_for_request")


def _get_cache_key_namespace(cache_key):
    """
    Split the given cache key by the first colon to get a namespace.

    :param cache_key: Cache key string
    :type cache_key: str
    :return: Cache namespace string
    :rtype: str
    """
    return force_str(cache_key).split(str(":"), 1)[0]


def get_cache_duration(cache_key):
    """
    Determine a cache duration for the given cache key.

    :param cache_key: Cache key string
    :type cache_key: str
    :return: Timeout seconds
    :rtype: int
    """
    namespace = _get_cache_key_namespace(cache_key)
    duration = settings.SHUUP_CACHE_DURATIONS.get(namespace)
    if duration is None:
        duration = DEFAULT_CACHE_DURATIONS.get(namespace, settings.SHUUP_DEFAULT_CACHE_DURATION)
    return duration


class VersionedCache(object):
    def __init__(self, using):
        """
        :param using: Cache alias
        :type using: str
        """
        self.using = using
        self._cache = caches[self.using]

    def bump_version(self, cache_key):
        """
        Bump up the cache version for the given cache key/namespace.

        :param cache_key: Cache key or namespace
        :type cache_key: str
        """
        namespace = _get_cache_key_namespace(cache_key)
        version = str("%s/%s" % (time.time(), random.random()))
        self.set(str("_version:") + namespace, version)
        setattr(_versions, namespace, version)

    def get_version(self, cache_key):
        """
        Get the cache version (or None) for the given cache key/namespace.

        The cache version is stored in thread-local storage for the
        current request, so unless bumped in-request, all gets within a
        single request should get coherently versioned data from the
        cache.

        :param cache_key: Cache key or namespace
        :type cache_key: str
        :return: Version ID or none
        :rtype: str|None
        """
        namespace = _get_cache_key_namespace(cache_key)
        if not hasattr(_versions, namespace):
            version = self._cache.get(str("_version:") + namespace)
            setattr(_versions, namespace, version)
        else:
            version = getattr(_versions, namespace, None)
        return version

    def set(self, key, value, timeout=None, version=None):
        """
        Set the value for key `key` in the cache.

        Unlike ``django.core.caches[using].set()``, this also derives
        timeout and versioning information from the key (and cached
        version data) if the key begins with a colon-separated namespace,
        such as ``foo:bar``.

        :param key: Cache key
        :type key: str
        :param value: Value to cache
        :type value: object
        :param timeout: Timeout seconds or None (for auto-determination)
        :type timeout: int|None
        :param version: Version string or None (for auto-determination)
        :type version: str|None
        :param using: Cache alias
        :type using: str
        """
        if timeout is None:
            timeout = get_cache_duration(key)
        if version is None:
            version = self.get_version(key)
        try:
            self._cache.set(key, value, timeout=timeout, version=version)
        except PicklingError:
            LOGGER.exception(
                "Unable to set cache with key: {}, value: {!r}, value could not be pickled.".format(key, value)
            )

    def get(self, key, version=None, default=None):
        """
        Get the value for key `key` in the cache.

        Unlike `django.core.caches[using].get()`, versioning information
        can be auto-derived from the key (and cached version data) if the
        key begins with a colon-separated namespace, such as `foo:bar`.

        :param key: Cache key
        :type key: str
        :param version: Version string or None (for auto-determination)
        :type version: str|None
        :param default: Default value, if the key is not found
        :type default: object
        :param using: Cache alias
        :type using: str
        :return: cached value
        :rtype: object
        """
        if version is None:
            version = self.get_version(key)
        return self._cache.get(key, default=default, version=version)

    def clear(self):
        self._cache.clear()
