# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.test import override_settings
from django.utils.translation import activate

from shuup.admin.modules.services.forms import PaymentMethodForm
from shuup.admin.modules.shops.forms import ShopBaseForm, ShopWizardForm
from shuup.testing.factories import get_default_payment_method, get_default_shop
from shuup.testing.utils import apply_request_middleware
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
    assert shop_form.languages[0] == "fi"
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


@pytest.mark.django_db
def test_model_form_partially_translated(rf, admin_user):
    with override_settings(
        **{"LANGUAGES": (("en", "en"), ("fi", "fi"), ("ja", "ja")), "PARLER_DEFAULT_LANGUAGE_CODE": "en"}
    ):
        activate("en")
        get_default_shop()
        request = apply_request_middleware(rf.get("/"), user=admin_user)
        test_name_en = "Test shop"
        payment_method = get_default_payment_method()
        payment_method.name = test_name_en
        payment_method.save()

        form = PaymentMethodForm(instance=payment_method, request=request, languages=settings.LANGUAGES)
        data = get_form_data(form, prepared=True)
        assert data.get("name__en") == test_name_en
        assert not data.get("name__fi")
        form = PaymentMethodForm(data=data, instance=payment_method, request=request, languages=settings.LANGUAGES)
        form.full_clean()
        assert form.is_valid() and not form.errors
        payment_method = form.save()

        # Add description for Finnish and and name in Finnish should be required
        with override_settings(**{"PARLER_DEFAULT_LANGUAGE_CODE": "fi"}):
            data["description__fi"] = "Some description"
            form = PaymentMethodForm(data=data, instance=payment_method, request=request, languages=settings.LANGUAGES)
            form.full_clean()
            assert not form.is_valid() and form.errors

        test_name_fi = "Some method name in finnish"
        data["name__fi"] = test_name_fi
        form = PaymentMethodForm(data=data, instance=payment_method, request=request, languages=settings.LANGUAGES)
        form.full_clean()
        assert form.is_valid() and not form.errors
        payment_method = form.save()

        assert payment_method.name == test_name_en, "Object in English"

        activate("fi")
        payment_method.set_current_language("fi")
        assert payment_method.name == test_name_fi, "Object in Finnish"

        activate("ja")
        payment_method.set_current_language("ja")
        assert payment_method.name == test_name_en, "Should fallback to English"

        # Check that no sneaky translations is not created for Japan
        with pytest.raises(ObjectDoesNotExist):
            translation = payment_method.get_translation("ja")
            translation.refresh_from_db()  # Just in case if the translation object comes from cache or something

        # Empty finnish translations and see if Finnish starts fallbacks too
        data["name__fi"] = data["description__fi"] = ""
        form = PaymentMethodForm(data=data, instance=payment_method, request=request, languages=settings.LANGUAGES)
        form.full_clean()
        assert form.is_valid() and not form.errors
        form.save()

        # Check that no sneaky translations is not created for Finnish
        with pytest.raises(ObjectDoesNotExist):
            translation = payment_method.get_translation("fi")
            translation.refresh_from_db()  # Just in case if the translation object comes from cache or something


@pytest.mark.django_db
def test_form_labels():
    shop_form = ShopBaseForm(languages=[("en", "en")])
    assert shop_form.base_fields["name__en"].label == "Name"

    shop_form = ShopBaseForm(languages=[("en", "en"), ("fi", "fi")])
    assert shop_form.base_fields["name__en"].label == "Name [English]"
    assert shop_form.base_fields["name__fi"].label == "Name [Finnish]"

    shop_form = ShopWizardForm(languages=[("en", "en"), ("fi", "fi")])
    assert shop_form.base_fields["public_name__en"].label == "Shop name [English]"
    assert shop_form.base_fields["public_name__fi"].label == "Shop name [Finnish]"
