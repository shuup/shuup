# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import parler.appsettings
import pytest

from shuup.core.models import CustomCarrier, ServiceProvider

caching_was_enabled = None


def setup_module(module):
    # override_settings does to work with parler, since it does not read
    # django.conf.settings but parler.appsettings
    global caching_was_enabled
    caching_was_enabled = parler.appsettings.PARLER_ENABLE_CACHING
    parler.appsettings.PARLER_ENABLE_CACHING = False


def teardown_module(module):
    parler.appsettings.PARLER_ENABLE_CACHING = caching_was_enabled


@pytest.mark.django_db
def test_service_provider_name_is_translatable():
    obj = CustomCarrier.objects.create()
    obj.set_current_language("en")
    obj.name = "Car"
    obj.set_current_language("se")
    obj.name = "Bil"
    obj.save()

    obj.set_current_language("en")
    assert obj.name == "Car"

    obj.set_current_language("se")
    assert obj.name == "Bil"

    found = ServiceProvider.objects.get(pk=obj.pk)
    found.set_current_language("en")
    assert found.name == "Car"
    found.set_current_language("se")
    assert found.name == "Bil"


@pytest.mark.django_db
def test_service_provider_translations_get_saved():
    obj = CustomCarrier.objects.language("en").create(name="Car")
    obj.set_current_language("se")
    obj.name = "Bil"
    assert set(obj.get_available_languages(include_unsaved=True)) == set(["en", "se"])
    assert set(obj.get_available_languages()) == set(["en"])
    obj.save()
    assert set(obj.get_available_languages()) == set(["en", "se"])
    assert ServiceProvider.objects.language("en").get(pk=obj.pk).name == "Car"
    assert ServiceProvider.objects.language("se").get(pk=obj.pk).name == "Bil"


@pytest.mark.django_db
def test_service_provider_default_manager():
    """
    Default manager of ServiceProvider is polymorphic and translatable.
    """
    obj = CustomCarrier.objects.language("en").create(name="Car")
    obj.set_current_language("se")
    obj.name = "Bil"
    obj.save()
    assert type(obj) == CustomCarrier

    found = ServiceProvider.objects.language("en").get(pk=obj.pk)
    assert found == obj
    assert type(found) == CustomCarrier
    assert found.name == "Car"

    found = ServiceProvider.objects.language("se").get(pk=obj.pk)
    assert found == obj
    assert type(found) == CustomCarrier
    assert found.name == "Bil"

    found.set_current_language("en")
    assert found.name == "Car"

    found.set_current_language("se")
    assert found.name == "Bil"

    found = ServiceProvider.objects.translated("en", name="Car").get(pk=obj.pk)
    assert found == obj
    assert type(found) == CustomCarrier

    found = ServiceProvider.objects.translated("se", name="Bil").get(pk=obj.pk)
    assert found == obj
    assert type(found) == CustomCarrier


@pytest.mark.django_db
def test_service_provider_base_manager():
    """
    Base manager of ServiceProvider is translatable.
    """
    obj = CustomCarrier.objects.language("en").create(name="Car")
    found = ServiceProvider.objects.non_polymorphic().language("en").get(pk=obj.pk)
    assert found.pk == obj.pk
    assert type(found) == ServiceProvider
