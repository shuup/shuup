# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
"""
API for Shuup's Dynamic Configuration.

Idea of the Dynamic Configuration is to allow storing configuration
values similarly as :ref:`Django settings <django-settings-module>`
allows, but in a more flexible way: Dynamic Configuration can be changed
with a simple API and there is no need restart the application server
after changing a value.

Dynamic configuration values are permanent.  Current implementation
stores the values with `~shuup.core.models.ConfigurationItem` model into
database, but that may change in the future.

Configuration values are get and set by a key string.  There is a global
configuration and a shop specific configuration for each shop.  Values
in shop specific configuration override the values in global
configuration.
"""
from __future__ import unicode_literals

from shuup.core import cache
from shuup.core.models import ConfigurationItem, EncryptedConfigurationItem


def set(shop, key, value, encrypted=False):
    """
    Set configuration item value for a shop or globally.

    If given `shop` is ``None``, the value of given `key` is set
    globally for all shops.  Otherwise sets a shop specific value which
    overrides the global value in configuration of the specified shop.

    :param shop: Shop to set value for, or None to set a global value
    :type shop: shuup.core.models.Shop|None
    :param key: Name of the key to set
    :type key: str
    :param value: Value to set.  Note: Must be JSON serializable.
    :type value: Any
    """
    if not encrypted:
        ConfigurationItem.objects.update_or_create(shop=shop, key=key, defaults={"value": value})
    else:
        EncryptedConfigurationItem.objects.update_or_create(shop=shop, key=key, defaults={"value": value})
    if shop:
        cache.set(_get_cache_key(shop), None)
    else:
        cache.bump_version(_SHOP_CONF_NAMESPACE)


def get(shop, key, default=None):
    """
    Get configuration value by shop and key.

    Global configuration can be accessed with ``shop=None``.

    :param shop: Shop to get configuration value for, or None
    :type shop: shuup.core.models.Shop|None
    :param key: Configuration item key
    :type key: str
    :param default:
      Default value returned if no value is set for given key (globally
      or in given shop).
    :type default: Any
    :return: Configuration value or the default value
    :rtype: Any
    """
    return _get_configuration(shop).get(key, default)


def _get_configuration(shop):
    """
    Get global or shop specific configuration with caching.

    :param shop: Shop to get configuration for, or None
    :type shop: shuup.core.models.Shop|None
    :return: Global or shop specific configuration
    :rtype: dict
    """
    configuration = cache.get(_get_cache_key(shop))
    if configuration is None:
        configuration = _cache_shop_configuration(shop)
    return configuration


def _cache_shop_configuration(shop):
    """
    Cache global or shop specific configuration.

    Global configuration (`shop` is ``None``) is read first, then `shop`
    based configuration is updated over that.

    :param shop: Shop to cache configuration for, or None
    :type shop: shuup.core.models.Shop|None
    :return: Cached configuration
    :rtype: dict
    """
    configuration = {}
    configuration.update(_get_configuration_from_db(None))
    if shop:
        configuration.update(_get_configuration_from_db(shop))
    cache.set(_get_cache_key(shop), configuration)
    return configuration


def _get_configuration_from_db(shop):
    """
    Get global or shop specific configuration from database.

    :param shop: Shop to fetch configuration for, or None
    :type shop: shuup.core.models.Shop|None
    :return: Configuration as it was saved in database
    :rtype: dict
    """
    configuration = {}
    for conf_item in ConfigurationItem.objects.filter(shop=shop):
        configuration[conf_item.key] = conf_item.value
    for conf_item in EncryptedConfigurationItem.objects.filter(shop=shop):
        configuration[conf_item.key] = conf_item.value
    return configuration


_SHOP_CONF_NAMESPACE = str("shop_config")


def _get_cache_key(shop):
    """
    Get global or shop specific cache key.

    :param shop: Shop to get cache key for, or None
    :type shop: shuup.core.models.Shop|None
    :return: Global or shop specific cache key
    :rtype: str
    """
    return str("%s:%s") % (_SHOP_CONF_NAMESPACE, shop.pk if shop else 0)
