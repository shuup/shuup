# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from django.conf import settings
from django.test import override_settings
from django.utils.translation import activate

from shuup.testing.factories import get_default_shop
from shuup.admin.modules.shops.views.edit import ShopBaseForm
from shuup_tests.utils.forms import get_form_data


@pytest.mark.django_db
@override_settings(**{"LANGUAGES": (("en", "en"), ("fi", "fi")), "PARLER_DEFAULT_LANGUAGE_CODE": "fi"})
def test_default_language_finnish():
    activate("en")
    test_name_en = "Test shop"
    test_name_fi = "Testi kauppa"
    shop = get_default_shop()
    shop.name = test_name_en
    shop.public_name = test_name_en
    shop.save()

    shop_form = ShopBaseForm(instance=shop, languages=settings.LANGUAGES)
    data = get_form_data(shop_form, prepared=True)
    assert data.get("name__en") == test_name_en
    assert not data.get("name__fi")
    shop_form = ShopBaseForm(data=data, instance=shop, languages=settings.LANGUAGES)
    shop_form.full_clean()
    assert not shop_form.is_valid() and shop_form.errors

    data["name__fi"] = test_name_fi
    data["public_name__fi"] = test_name_fi
    shop_form = ShopBaseForm(data=data, instance=shop, languages=settings.LANGUAGES)
    shop_form.full_clean()
    assert shop_form.is_valid() and not shop_form.errors
    shop_form.save()

    shop.set_current_language("en")
    assert shop.name == test_name_en, "English activated"
    shop.set_current_language("fi")
    assert shop.name == test_name_fi, "Finnish activated"


@pytest.mark.django_db
@override_settings(**{"LANGUAGES": (("en", "en"), ("fi", "fi")), "PARLER_DEFAULT_LANGUAGE_CODE": "en"})
def test_default_language_english():
    activate("en")
    test_name_en = "Test shop"
    shop = get_default_shop()
    shop.name = test_name_en
    shop.public_name = test_name_en
    shop.save()

    shop_form = ShopBaseForm(instance=shop, languages=settings.LANGUAGES)
    data = get_form_data(shop_form, prepared=True)
    assert data.get("name__en") == test_name_en
    assert not data.get("name__fi")
    shop_form = ShopBaseForm(data=data, instance=shop, languages=settings.LANGUAGES)
    shop_form.full_clean()
    assert shop_form.is_valid() and not shop_form.errors
