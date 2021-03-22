# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import parler.appsettings
import pytest
from filer.models import Folder, Image

from shuup.core.models import Shop, ShopStatus
from shuup.testing.factories import DEFAULT_IDENTIFIER, DEFAULT_NAME, create_random_user, get_shop

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
def test_shop_wont_be_deleted():
    shop = Shop.objects.create(
        name=DEFAULT_NAME, identifier="zoombie", status=ShopStatus.ENABLED, public_name=DEFAULT_NAME
    )

    folder = Folder.objects.create(name="Root")
    img = Image.objects.create(name="imagefile", folder=folder)

    shop.logo = img
    shop.save()
    img.delete()

    assert Shop.objects.filter(pk=shop.pk).exists()


@pytest.mark.django_db
def test_shop_translations_get_saved():
    obj = Shop.objects.language("en").create(name="Store")
    obj.set_current_language("fi")
    obj.name = "Liike"
    assert set(obj.get_available_languages(include_unsaved=True)) == set(["en", "fi"])
    assert set(obj.get_available_languages()) == set(["en"])
    obj.save()
    assert set(obj.get_available_languages()) == set(["en", "fi"])
    assert Shop.objects.language("en").get(pk=obj.pk).name == "Store"
    assert Shop.objects.language("fi").get(pk=obj.pk).name == "Liike"


@pytest.mark.django_db
def test_shop_translations_manager():
    shop = Shop.objects.language("en").create(name="Store")
    shop.set_current_language("fi")
    shop.name = "Liike"
    shop.save()

    found = Shop.objects.language("fi").get(pk=shop.pk)
    assert found == shop
    assert found.name == "Liike"

    found = Shop.objects.language("en").get(pk=shop.pk)
    assert found == shop
    assert found.name == "Store"

    found = Shop.objects.translated("fi", name="Liike").get(pk=shop.pk)
    assert found == shop

    found = Shop.objects.translated("en", name="Store").get(pk=shop.pk)
    assert found == shop


@pytest.mark.django_db
def test_shop_staff_members():
    shop1 = get_shop(True)
    shop2 = get_shop(True)
    staff = create_random_user()
    shop1.staff_members.add(staff)
    assert staff.shops.count() == 1
    staff.shops.set(Shop.objects.all())
    assert staff in shop2.staff_members.all()
    assert staff.shops.count() == 2
