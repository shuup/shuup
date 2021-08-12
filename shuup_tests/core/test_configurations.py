# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.test.utils import override_settings

from shuup import configuration
from shuup.core import cache
from shuup.core.models import ConfigurationItem, EncryptedConfigurationItem
from shuup.testing.factories import get_default_shop


@pytest.mark.django_db
def test_simple_set_and_get_with_shop():
    with override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "test_simple_set_and_get_with_shop",
            }
        }
    ):
        cache.init_cache()
        shop = get_default_shop()
        configuration.set(shop, "answer", 42)
        assert configuration.get(shop, "answer") == 42

        assert configuration.get(shop, "non-existing") is None
        configuration.set(shop, "non-existing", "hello")
        assert configuration.get(shop, "non-existing") == "hello"


@pytest.mark.django_db
def test_simple_set_and_get_without_shop():
    with override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "test_simple_set_and_get_without_shop",
            }
        }
    ):
        cache.init_cache()
        configuration.set(None, "answer", 42)
        assert configuration.get(None, "answer") == 42

        assert configuration.get(None, "non-existing") is None
        configuration.set(None, "non-existing", "hello")
        assert configuration.get(None, "non-existing") == "hello"

        configuration.set(None, "encrypted-key", "encrypted-value", encrypted=True)
        assert configuration.get(None, "encrypted-key") == "encrypted-value"
        assert EncryptedConfigurationItem.objects.filter(shop=None, key="encrypted-key").exists()
        assert not ConfigurationItem.objects.filter(shop=None, key="encrypted-key").exists()


@pytest.mark.django_db
def test_simple_set_and_get_cascading():
    with override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "test_simple_set_and_get_cascading",
            }
        }
    ):
        cache.init_cache()
        shop = get_default_shop()
        configuration.set(None, "answer", 42)
        assert configuration.get(None, "answer") == 42
        assert configuration.get(shop, "answer", 42)

        assert configuration.get(None, "non-existing") is None
        assert configuration.get(shop, "non-existing") is None
        configuration.set(shop, "non-existing", "hello")
        assert configuration.get(None, "non-existing") is None
        assert configuration.get(shop, "non-existing") == "hello"

        assert configuration.get(None, "foo") is None
        assert configuration.get(shop, "foo") is None
        configuration.set(None, "foo", "bar")
        configuration.set(shop, "foo", "baz")
        assert configuration.get(None, "foo") == "bar"
        assert configuration.get(shop, "foo") == "baz"


@pytest.mark.django_db
def test_configuration_gets_saved():
    with override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "test_configuration_gets_saved",
            }
        }
    ):
        cache.init_cache()
        configuration.set(None, "x", 1)
        assert configuration.get(None, "x") == 1
        configuration.set(None, "x", 2)
        assert configuration.get(None, "x") == 2
        configuration.set(None, "x", 3)
        assert configuration.get(None, "x") == 3
        conf_item = ConfigurationItem.objects.get(shop=None, key="x")
        assert conf_item.value == 3


@pytest.mark.django_db
def test_configuration_set_and_get():
    with override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "test_configuration_set_and_get",
            }
        }
    ):
        cache.init_cache()
        shop = get_default_shop()
        test_conf_data = {"data": "test"}
        configuration.set(shop, "key", test_conf_data)

        # Get the configuration via configuration API
        assert configuration.get(shop, "key") == test_conf_data
        # Check that configuration is saved to database
        assert ConfigurationItem.objects.get(shop=shop, key="key").value == test_conf_data


@pytest.mark.django_db
def test_configuration_update():
    with override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "test_configuration_update",
            }
        }
    ):
        cache.init_cache()
        shop = get_default_shop()
        configuration.set(shop, "key1", {"data": "test1"})
        configuration.set(shop, "key2", {"data": "test2"})
        configuration.set(shop, "key3", {"data": "test3"})
        assert configuration.get(shop, "key1").get("data") == "test1"
        assert configuration.get(shop, "key3").get("data") == "test3"

        # Update configuration
        configuration.set(shop, "key3", {"data": "test_bump"})
        assert configuration.get(shop, "key3").get("data") == "test_bump"


@pytest.mark.django_db
def test_global_configurations():
    with override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "test_global_configurations",
            }
        }
    ):
        cache.init_cache()
        shop = get_default_shop()
        configuration.set(None, "key1", {"data": "test1"})
        configuration.set(shop, "key2", {"data": "test2"})

        # key1 from shop should come from global configuration
        assert configuration.get(shop, "key1").get("data") == "test1"
        # key2 shouldn't be in global configurations
        assert configuration.get(None, "key2") is None

        # Update global configuration
        configuration.set(None, "key1", {"data": "test_bump"})
        assert configuration.get(shop, "key1").get("data") == "test_bump"

        # Override shop data for global key1
        configuration.set(shop, "key1", "test_data")
        assert configuration.get(shop, "key1") == "test_data"

        # Update shop configuration for global key1
        configuration.set(shop, "key1", "test_data1")
        assert configuration.get(shop, "key1") == "test_data1"


@pytest.mark.django_db
def test_configuration_cache():
    with override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "test_configuration_cache",
            }
        }
    ):
        cache.init_cache()

        shop = get_default_shop()
        configuration.set(None, "key1", "test1")
        configuration.set(shop, "key2", "test2")

        # Shop configurations cache should be bumped
        assert cache.get(configuration._get_cache_key(shop)) is None
        configuration.get(shop, "key1")
        # Now shop configurations and key2 should found from cache
        assert cache.get(configuration._get_cache_key(shop)).get("key2") == "test2"
