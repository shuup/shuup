# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import django.template
import json
import pytest
import reversion
from bs4 import BeautifulStoneSoup
from django.conf import settings
from django.test.utils import override_settings
from django.utils.translation import activate

from shuup.core.models import ShopStatus
from shuup.gdpr.models import GDPRCookieCategory, GDPRSettings
from shuup.gdpr.utils import (
    create_user_consent_for_all_documents,
    ensure_gdpr_privacy_policy,
    is_documents_consent_in_sync,
)
from shuup.testing import factories
from shuup.utils.django_compat import reverse
from shuup.xtheme.models import Snippet, SnippetType
from shuup_tests.utils import SmartClient


def assert_update(client, url, expected):
    response = client.get(url)
    response_content = response.content.decode("utf-8")
    if expected:
        assert "privacy-policy-update" in response_content
    else:
        assert "privacy-policy-update" not in response_content


@pytest.mark.django_db
def test_resource_injection(client):
    """
    Test that the GDPR warning is injected into the front template when enabled
    """
    activate("en")
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
        cookies="cookie1,cookie2,_cookie3",
        name="RequiredCookies",
        how_is_used="to make the site work",
    )
    default_active_cookie_category = GDPRCookieCategory.objects.create(
        shop=shop,
        always_active=False,
        default_active=True,
        cookies="analyticsCookie",
        name="Analytics",
        how_is_used="to track users",
    )
    response, soup = client.response_and_soup(index_url)
    response_content = response.content.decode("utf-8")
    assert "gdpr-consent-warn-bar" in response_content
    assert cookie_category.cookies in response_content
    assert cookie_category.name in response_content
    assert cookie_category.how_is_used in response_content
    default_active_input = soup.find("input", {"name": "cookie_category_%d" % default_active_cookie_category.pk})
    assert default_active_input.has_attr("checked")

    # make sure no other shop has this
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        shop2 = factories.get_shop(identifier="shop2", status=ShopStatus.DISABLED, domain="shop2")
        response = client.get(index_url, HTTP_HOST=shop2.domain)
        response_content = response.content.decode("utf-8")
        assert "gdpr-consent-warn-bar" not in response_content


@pytest.mark.django_db
def test_update_injection():
    shop = factories.get_default_shop()
    client = SmartClient()
    index_url = reverse("shuup:index")

    page = ensure_gdpr_privacy_policy(shop)
    shop_gdpr = GDPRSettings.get_for_shop(shop)
    shop_gdpr.enabled = True
    shop_gdpr.privacy_policy = page
    shop_gdpr.save()

    assert_update(client, index_url, False)  # nothing consented in past, should not show

    user = factories.create_random_user("en")
    password = "test"
    user.set_password(password)
    user.save()

    client.login(username=user.username, password=password)
    assert_update(client, index_url, False)  # no consent given, should not be visible

    create_user_consent_for_all_documents(shop, user)
    assert_update(client, index_url, False)

    with reversion.create_revision():
        page.save()

    assert not is_documents_consent_in_sync(shop, user)
    assert_update(client, index_url, True)

    # consent
    client.get(reverse("shuup:gdpr_policy_consent", kwargs=dict(page_id=page.pk)))
    assert is_documents_consent_in_sync(shop, user)
    assert_update(client, index_url, False)


@pytest.mark.django_db
def test_consent_cookies(rf):
    """
    Test that the GDPR consent is generated and saved into a cooki
    """
    for code, lang in settings.LANGUAGES:
        activate(code)
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
            how_is_used="to make the site work",
        )
        optional_cookie_category = GDPRCookieCategory.objects.create(
            shop=shop,
            always_active=False,
            cookies="_opt1,_opt2,_opt3",
            name="OptionalCookies",
            how_is_used="to spy users",
        )
        default_active_cookie_category = GDPRCookieCategory.objects.create(
            shop=shop,
            always_active=False,
            default_active=True,
            cookies="_analytics",
            name="Analytics",
            how_is_used="to track users",
        )

        # create privacy policy GDPR document
        privacy_policy = ensure_gdpr_privacy_policy(shop)
        response = client.get(index_url)
        assert settings.SHUUP_GDPR_CONSENT_COOKIE_NAME not in response.cookies

        # send consent
        response = client.post(
            reverse("shuup:gdpr_consent"),
            data={
                "cookie_category_{}".format(required_cookie_category.id): "on",
                "cookie_category_{}".format(optional_cookie_category.id): "on",
                "cookie_category_{}".format(default_active_cookie_category.id): "on",
            },
        )

        assert settings.SHUUP_GDPR_CONSENT_COOKIE_NAME in response.cookies
        cookies_data = json.loads(response.cookies[settings.SHUUP_GDPR_CONSENT_COOKIE_NAME].value)
        assert privacy_policy.id == cookies_data["documents"][0]["id"]
        assert privacy_policy.url == cookies_data["documents"][0]["url"]

        for cookie in required_cookie_category.cookies.split(","):
            assert cookie in cookies_data["cookies"]
        for cookie in optional_cookie_category.cookies.split(","):
            assert cookie in cookies_data["cookies"]
        for cookie in default_active_cookie_category.cookies.split(","):
            assert cookie in cookies_data["cookies"]

        engine = django.template.engines["jinja2"]
        template = engine.from_string("{{ gdpr.get_accepted_cookies()|json }}")

        request = rf.get("/")
        context = {"request": request}
        rendered_cookies = json.loads(template.render(context))
        assert rendered_cookies == []

        request.COOKIES = {
            settings.SHUUP_GDPR_CONSENT_COOKIE_NAME: (
                response.client.cookies[settings.SHUUP_GDPR_CONSENT_COOKIE_NAME].value
            )
        }
        context = {"request": request}
        rendered_cookies = set(json.loads(template.render(context)))
        assert rendered_cookies == set(["_opt2", "cookie1", "_cookie3", "_opt3", "_analytics", "cookir2", "_opt1"])


@pytest.mark.django_db
def test_consent_block_snippet_injection(rf):
    """
    Test that the GDPR consent is required to inject xtheme scripts
    """
    shop = factories.get_default_shop()

    client = SmartClient()
    index_url = reverse("shuup:index")

    # create a GDPR setting for the shop
    shop_gdpr = GDPRSettings.get_for_shop(shop)
    shop_gdpr.cookie_banner_content = "my cookie banner content"
    shop_gdpr.cookie_privacy_excerpt = "my cookie privacyexcerpt"
    shop_gdpr.enabled = True
    shop_gdpr.save()

    # configure some snippets to be injected
    google_snippet = Snippet.objects.create(
        name="Google Analytics",
        snippet_type=SnippetType.InlineHTMLMarkup,
        location="body_end",
        shop=shop,
        snippet='<script id="google-script"></script>',
    )

    facebook_snippet = Snippet.objects.create(
        name="Facebook Pixel",
        snippet_type=SnippetType.InlineHTMLMarkup,
        location="body_end",
        shop=shop,
        snippet='<script id="facebook-script"></script>',
    )

    # create cookie categories
    required_cookie_category = GDPRCookieCategory.objects.create(
        shop=shop,
        always_active=True,
        cookies="cookie1,cookir2,_cookie3",
        name="RequiredCookies",
        how_is_used="to make the site work",
    )
    google_cookie_category = GDPRCookieCategory.objects.create(
        shop=shop,
        always_active=False,
        cookies="_google",
        name="GoogleCookies",
        how_is_used="to spy users",
    )
    google_cookie_category.block_snippets.add(google_snippet)

    faceboook_cookie_category = GDPRCookieCategory.objects.create(
        shop=shop,
        always_active=False,
        cookies="_facebook",
        name="Facebook",
        how_is_used="to track users",
    )
    faceboook_cookie_category.block_snippets.add(facebook_snippet)

    # create privacy policy GDPR document
    ensure_gdpr_privacy_policy(shop)
    response = client.get(index_url)
    assert settings.SHUUP_GDPR_CONSENT_COOKIE_NAME not in response.cookies

    # send consent only for the required and google
    response = client.post(
        reverse("shuup:gdpr_consent"),
        data={
            "cookie_category_{}".format(required_cookie_category.id): "on",
            "cookie_category_{}".format(google_cookie_category.id): "on",
            "cookie_category_{}".format(faceboook_cookie_category.id): "off",
        },
    )

    assert settings.SHUUP_GDPR_CONSENT_COOKIE_NAME in response.cookies
    cookies_data = json.loads(response.cookies[settings.SHUUP_GDPR_CONSENT_COOKIE_NAME].value)

    for cookie in required_cookie_category.cookies.split(","):
        assert cookie in cookies_data["cookies"]
    for cookie in google_cookie_category.cookies.split(","):
        assert cookie in cookies_data["cookies"]
    for cookie in faceboook_cookie_category.cookies.split(","):
        assert cookie not in cookies_data["cookies"]

    # send the request again, only the google script should be injected
    response = client.get(index_url)
    response.render()

    content = BeautifulStoneSoup(response.content)
    assert content.find_all("script", attrs={"id": "google-script"})
    assert not content.find_all("script", attrs={"id": "facebook-script"})
