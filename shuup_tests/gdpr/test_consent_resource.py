# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json

import pytest
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.utils.timezone import now

from shuup.core.models import ShopStatus
from shuup.gdpr.models import GDPRCookieCategory, GDPRSettings
from shuup.simple_cms.models import Page, PageType
from shuup.testing import factories
from shuup_tests.utils import SmartClient


@pytest.mark.django_db
def test_resouce_injection(client):
    """
    Test that the GDPR warning is injected into the front template when enabled
    """
    shop = factories.get_default_shop()
    client = SmartClient()
    index_url = reverse("shuup:index")
    response = client.get(index_url)
    assert "gdpr-consent-warn-bar" not in response.content.decode("utf-8")

    # create a GDPR setting for the shop
    shop_gdpr = GDPRSettings.get_for_shop(shop)
    shop_gdpr.cookie_banner_content = "my cookie banner content"
    shop_gdpr.cookie_privacy_excerpt = " my cookie privacyexcerpt"
    shop_gdpr.enabled = True
    shop_gdpr.save()

    # the contents should be injected in the html
    response = client.get(index_url)
    response_content = response.content.decode("utf-8")
    assert "gdpr-consent-warn-bar" in response_content
    assert shop_gdpr.cookie_banner_content in response_content
    assert shop_gdpr.cookie_privacy_excerpt in response_content

    # create cookie categories
    cookie_category = GDPRCookieCategory.objects.create(
        shop=shop,
        always_active=True,
        cookies="cookie1,cookir2,_cookie3",
        name="RequiredCookies",
        how_is_used="to make the site work"
    )
    response = client.get(index_url)
    response_content = response.content.decode("utf-8")
    assert "gdpr-consent-warn-bar" in response_content
    assert cookie_category.cookies in response_content
    assert cookie_category.name in response_content
    assert cookie_category.how_is_used in response_content

    # make sure no other shop has this
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        shop2 = factories.get_shop(identifier="shop2", status=ShopStatus.DISABLED, domain="shop2")
        response = client.get(index_url, HTTP_HOST=shop2.domain)
        response_content = response.content.decode("utf-8")
        assert "gdpr-consent-warn-bar" not in response_content


@pytest.mark.django_db
def test_consent_cookies(client):
    """
    Test that the GDPR consent is generated and saved into a cooki
    """
    shop = factories.get_default_shop()
    client = SmartClient()
    index_url = reverse("shuup:index")
    response = client.get(index_url)

    # create a GDPR setting for the shop
    shop_gdpr = GDPRSettings.get_for_shop(shop)
    shop_gdpr.cookie_banner_content = "my cookie banner content"
    shop_gdpr.cookie_privacy_excerpt = "my cookie privacyexcerpt"
    shop_gdpr.enabled = True
    shop_gdpr.save()

    # create cookie categories
    required_cookie_category = GDPRCookieCategory.objects.create(
        shop=shop,
        always_active=True,
        cookies="cookie1,cookir2,_cookie3",
        name="RequiredCookies",
        how_is_used="to make the site work"
    )
    optional_cookie_category = GDPRCookieCategory.objects.create(
        shop=shop,
        always_active=False,
        cookies="_opt1,_opt2,_opt3",
        name="OptionalCookies",
        how_is_used="to spy users"
    )

    # create privacy policy GDPR document
    privacy_policy = Page.objects.create(
        shop=shop,
        title="Privacy policy",
        url="privacy-policy",
        page_type=PageType.REVISIONED,
        content="you just agree",
        available_from=now()
    )
    response = client.get(index_url)
    assert settings.SHUUP_GDPR_CONSENT_COOKIE_NAME not in response.cookies

    # send consent
    response = client.post(reverse("shuup:gdpr_consent"), data={
        "cookie_category_{}".format(required_cookie_category.id): "on",
        "cookie_category_{}".format(optional_cookie_category.id): "on"
    })

    assert settings.SHUUP_GDPR_CONSENT_COOKIE_NAME in response.cookies
    cookies_data = json.loads(response.cookies[settings.SHUUP_GDPR_CONSENT_COOKIE_NAME].value)
    assert privacy_policy.id == cookies_data["documents"][0]["id"]
    assert privacy_policy.url == cookies_data["documents"][0]["url"]

    for cookie in required_cookie_category.cookies.split(","):
        assert cookie in cookies_data["cookies"]
    for cookie in optional_cookie_category.cookies.split(","):
        assert cookie in cookies_data["cookies"]
