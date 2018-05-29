# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.urlresolvers import reverse
from django.utils.timezone import now
from django.utils.translation import activate

from shuup.gdpr.models import GDPRSettings
from shuup.simple_cms.models import Page, PageType
from shuup.testing import factories
from shuup_tests.utils import SmartClient


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
    privacy_policy = Page.objects.create(
        shop=shop,
        title="Privacy policy",
        url="privacy-policy",
        page_type=PageType.GDPR_CONSENT_DOCUMENT,
        content="you just agree",
        available_from=now()
    )

    redirect_target = "/redirect-success/"
    client = SmartClient()

    # user didn't checked the privacy policy agreement
    response = client.post(reverse("shuup:login"), data={
        "username": user.email,
        "password": "1234",
        REDIRECT_FIELD_NAME: redirect_target
    })
    assert response.status_code == 200
    assert "You must accept to this to authenticate" in response.content.decode("utf-8")

    response = client.post(reverse("shuup:login"), data={
        "username": user.email,
        "password": "1234",
        "accept_%d" % privacy_policy.id: "on",
        REDIRECT_FIELD_NAME: redirect_target
    })
    assert response.status_code == 302
    assert response.get("location")
    assert response.get("location").endswith(redirect_target)


@pytest.mark.django_db
def test_register_form(client):
    activate("en")
    shop = factories.get_default_shop()

    gdpr_settings = GDPRSettings.get_for_shop(shop)
    gdpr_settings.enabled = True
    gdpr_settings.save()

    # create privacy policy GDPR document
    privacy_policy = Page.objects.create(
        shop=shop,
        title="Privacy policy",
        url="privacy-policy",
        page_type=PageType.GDPR_CONSENT_DOCUMENT,
        content="you just agree",
        available_from=now()
    )

    redirect_target = "/index/"
    client = SmartClient()

    # user didn't checked the privacy policy agreement
    response = client.post(reverse("shuup:registration_register"), data={
        "username": "user",
        "email": "user@admin.com",
        "password1": "1234",
        "password2": "1234",
        REDIRECT_FIELD_NAME: redirect_target
    })
    assert response.status_code == 200
    assert "You must accept to this to register" in response.content.decode("utf-8")

    response = client.post(reverse("shuup:registration_register"), data={
        "username": "user",
        "email": "user@admin.com",
        "password1": "1234",
        "password2": "1234",
        "accept_%d" % privacy_policy.id: "on",
        REDIRECT_FIELD_NAME: redirect_target
    })
    assert response.status_code == 302
    assert response.get("location")
    assert response.get("location").endswith(redirect_target)
