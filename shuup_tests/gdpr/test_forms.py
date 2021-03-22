# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from bs4 import BeautifulSoup
from django.contrib.auth import REDIRECT_FIELD_NAME, get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import override_settings
from django.utils.translation import activate

from shuup.gdpr.models import GDPRSettings
from shuup.gdpr.providers import GDPRFieldProvider
from shuup.gdpr.utils import (
    create_user_consent_for_all_documents,
    ensure_gdpr_privacy_policy,
    is_documents_consent_in_sync,
)
from shuup.simple_cms.admin_module.views import PageForm
from shuup.simple_cms.models import Page
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import reverse
from shuup_tests.utils import SmartClient, printable_gibberish

User = get_user_model()


@pytest.mark.django_db
def test_authenticate_form(client):
    activate("en")
    shop = factories.get_default_shop()
    user = factories.create_random_user("en")
    user.email = "admin@admin.com"
    user.set_password("1234")
    user.save()

    gdpr_settings = GDPRSettings.get_for_shop(shop)
    gdpr_settings.enabled = True
    gdpr_settings.save()

    # create privacy policy GDPR document
    privacy_policy = ensure_gdpr_privacy_policy(shop)

    redirect_target = "/redirect-success/"
    client = SmartClient()

    login_url = reverse("shuup:login")
    response = client.get(login_url)
    soup = BeautifulSoup(response.content)
    login_form = soup.find("form", {"action": "/login/"})
    assert len(login_form.findAll("input")) == 5  # 4 + privacy policy checkbox

    # user didn't check the privacy policy agreement
    response = client.post(
        reverse("shuup:login"), data={"username": user.email, "password": "1234", REDIRECT_FIELD_NAME: redirect_target}
    )
    assert response.status_code == 200
    assert "You must accept this in order to authenticate." in response.content.decode("utf-8")

    response = client.post(
        reverse("shuup:login"),
        data={
            "username": user.email,
            "password": "1234",
            "accept_%d" % privacy_policy.id: "on",
            REDIRECT_FIELD_NAME: redirect_target,
        },
    )
    assert response.status_code == 302
    assert response.get("location")
    assert response.get("location").endswith(redirect_target)


@pytest.mark.django_db
def test_authenticate_form_without_consent_checkboxes(client):
    activate("en")
    shop = factories.get_default_shop()
    user = factories.create_random_user("en")
    user.email = "admin@admin.com"
    user.set_password("1234")
    user.save()

    consent_text = printable_gibberish()
    gdpr_settings = GDPRSettings.get_for_shop(shop)
    gdpr_settings.enabled = True
    gdpr_settings.skip_consent_on_auth = True
    gdpr_settings.auth_consent_text = consent_text
    gdpr_settings.save()

    # create privacy policy GDPR document
    privacy_policy = ensure_gdpr_privacy_policy(shop)

    redirect_target = "/redirect-success/"
    client = SmartClient()

    login_url = reverse("shuup:login")
    response = client.get(login_url)
    soup = BeautifulSoup(response.content)
    login_form = soup.find("form", {"action": "/login/"})
    assert len(login_form.findAll("input")) == 4
    assert consent_text in login_form.text

    # user didn't check the privacy policy agreement
    response = client.post(
        login_url, data={"username": user.email, "password": "1234", REDIRECT_FIELD_NAME: redirect_target}
    )
    assert response.status_code == 302


@pytest.mark.django_db
def test_register_form(client):
    activate("en")
    shop = factories.get_default_shop()

    gdpr_settings = GDPRSettings.get_for_shop(shop)
    gdpr_settings.enabled = True
    gdpr_settings.save()

    # create privacy policy GDPR document
    privacy_policy = ensure_gdpr_privacy_policy(shop)

    redirect_target = "/index/"
    client = SmartClient()

    # user didn't checked the privacy policy agreement
    response = client.post(
        reverse("shuup:registration_register"),
        data={
            "username": "user",
            "email": "user@admin.com",
            "password1": "1234",
            "password2": "1234",
            REDIRECT_FIELD_NAME: redirect_target,
        },
    )
    assert response.status_code == 200
    assert "You must accept this in order to register." in response.content.decode("utf-8")

    response = client.post(
        reverse("shuup:registration_register"),
        data={
            "username": "user",
            "email": "user@admin.com",
            "password1": "1234",
            "password2": "1234",
            "accept_%d" % privacy_policy.id: "on",
            REDIRECT_FIELD_NAME: redirect_target,
        },
    )
    assert response.status_code == 302
    assert response.get("location")
    assert response.get("location").endswith(redirect_target)

    user = User.objects.first()

    assert is_documents_consent_in_sync(shop, user)

    ensure_gdpr_privacy_policy(shop, force_update=True)
    assert not is_documents_consent_in_sync(shop, user)


@pytest.mark.django_db
def test_pageform_urls(rf, admin_user):
    shop = factories.get_default_shop()
    en_url = "test-url"
    fi_url = "test-fi-url"
    activate("en")
    request = apply_request_middleware(rf.post("/"), user=admin_user, shop=shop)
    with override_settings(LANGUAGES=[("en", "en"), ("fi", "fi")]):
        form = PageForm(request=request, data={"title__en": "test", "content__en": "test", "url__en": en_url})
        assert form.is_valid()
        assert form.is_url_valid("en", "url__en", en_url)
        assert form.is_url_valid("fi", "url__fi", fi_url)

        # create a page
        Page.objects.create(shop=shop, content="test", url=en_url, title="test")
        form = PageForm(
            request=request, data={"title__en": "test", "content__en": "test", "url__en": en_url, "url__fi": fi_url}
        )
        assert not form.is_valid()
        assert not form.is_url_valid("en", "url__en", en_url)
        assert form.is_url_valid("fi", "url__fi", fi_url)  # no changes in finnish, should be valid

        form = PageForm(request=request, data={"title__en": "test", "content__en": "test", "url__en": "new-url"})
        assert form.is_valid()
        assert form.is_url_valid("en", "url__en", "new-url")
        assert form.is_url_valid("fi", "url__fi", fi_url)


@pytest.mark.django_db
def test_field_provider(rf, admin_user):
    activate("en")
    shop = factories.get_default_shop()
    gdpr_settings = GDPRSettings.get_for_shop(shop)
    gdpr_settings.enabled = True
    gdpr_settings.save()
    # create privacy policy GDPR document
    privacy_policy = ensure_gdpr_privacy_policy(shop)
    page_consent_key = "accept_%d" % privacy_policy.pk

    request = apply_request_middleware(rf.post("/"), shop=shop, user=admin_user)
    field_provider = GDPRFieldProvider()

    # call twice.. the field should be there while the user hasn't consented to the page
    for test in range(2):
        fields = field_provider.get_fields(request=request)
        assert page_consent_key in [f.name for f in fields]

    # consent to the page, the field shouldn't be there
    create_user_consent_for_all_documents(shop, admin_user)
    fields = field_provider.get_fields(request=request)
    assert page_consent_key not in [f.name for f in fields]

    # change the document version - field must be there again
    privacy_policy.save()
    fields = field_provider.get_fields(request=request)
    assert page_consent_key in [f.name for f in fields]

    # check if the field is shown for anonymous
    request = apply_request_middleware(rf.post("/"), shop=shop, user=AnonymousUser())
    fields = field_provider.get_fields(request=request)
    assert page_consent_key in [f.name for f in fields]
