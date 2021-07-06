# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import pytest
from django.conf import settings
from django.utils.timezone import now
from django.utils.translation import activate

from shuup.core.models import PersonContact
from shuup.gdpr.models import GDPRCookieCategory, GDPRSettings
from shuup.simple_cms.models import Page
from shuup.testing import factories
from shuup.testing.soup_utils import extract_form_fields
from shuup.utils.django_compat import reverse
from shuup_tests.utils import SmartClient


@pytest.mark.django_db
def test_gdpr_admin_settings(client, admin_user):
    """
    Test that admin user can enable GDPR and add cookie categories
    """
    activate("en")
    shop = factories.get_default_shop()
    client = SmartClient()
    admin_user.set_password("admin")
    admin_user.save()
    client.login(username=admin_user.username, password="admin")
    admin_settings_url = reverse("shuup_admin:gdpr.settings")

    assert not GDPRSettings.objects.exists()
    response = client.soup(admin_settings_url)
    assert GDPRSettings.objects.exists()
    s = GDPRSettings.objects.first()
    assert s.cookie_banner_content == settings.SHUUP_GDPR_DEFAULT_BANNER_STRING
    assert s.cookie_privacy_excerpt == settings.SHUUP_GDPR_DEFAULT_EXCERPT_STRING
    assert GDPRCookieCategory.objects.count() == 0

    page = Page.objects.create(shop=shop, available_from=now())
    page.title = "test"
    page.save()
    # create the settings with only basic options
    payload = extract_form_fields(response)
    payload.pop("base-consent_pages")
    payload.update(
        {
            "base-enabled": True,
            "base-privacy_policy_page": page.pk,
            "base-cookie_banner_content__en": "Banner content",
            "base-cookie_privacy_excerpt__en": "Cookie excerpt",
            "cookie_categories-0-id": "",
            "cookie_categories-0-always_active": 1,
            "cookie_categories-0-name__en": "required",
            "cookie_categories-0-how_is_used__en": "to work",
            "cookie_categories-0-cookies": "sessionid",
            "cookie_categories-0-block_snippets": [],
        }
    )
    response = client.post(admin_settings_url, data=payload)
    assert response.status_code == 302

    assert GDPRCookieCategory.objects.count() == 1

    # add one more cookie category
    payload.update(
        {
            "cookie_categories-1-id": "",
            "cookie_categories-1-always_active": 1,
            "cookie_categories-1-name__en": "Maybe",
            "cookie_categories-1-how_is_used__en": "to spy",
            "cookie_categories-1-cookies": "_ga",
            "cookie_categories-1-block_snippets": [],
        }
    )
    client.post(admin_settings_url, data=payload)
    assert GDPRCookieCategory.objects.count() == 2


@pytest.mark.django_db
def test_gdpr_admin_download_data(client, admin_user):
    """
    Test that admin user can download customer data
    """
    activate("en")
    shop = factories.get_default_shop()
    customer = factories.create_random_person("en")
    product = factories.create_product("p1", shop, factories.get_default_supplier())
    [factories.create_random_order(customer, [product]) for order in range(3)]

    client = SmartClient()
    admin_user.set_password("admin")
    admin_user.save()
    client.login(username=admin_user.username, password="admin")
    admin_download_url = reverse("shuup_admin:gdpr.download_data", kwargs=dict(pk=customer.pk))
    response = client.post(admin_download_url)
    assert response.status_code == 200
    assert response._headers["content-disposition"][0] == "Content-Disposition"
    assert response._headers["content-disposition"][1].startswith("attachment; filename=user_data_")


@pytest.mark.django_db
def test_gdpr_admin_anonymize(client, admin_user):
    """
    Test that admin user can anonymize contact
    """
    activate("en")
    factories.get_default_shop()
    person = factories.create_random_person("en")
    person.user = factories.create_random_user("en")
    person.save()

    client = SmartClient()
    admin_user.set_password("admin")
    admin_user.save()
    client.login(username=admin_user.username, password="admin")
    admin_anonymize_url = reverse("shuup_admin:gdpr.anonymize", kwargs=dict(pk=person.pk))
    response = client.post(admin_anonymize_url)
    assert response.status_code == 302
    assert response.url.endswith(reverse("shuup_admin:contact.detail", kwargs=dict(pk=person.pk)))

    anonymized_person = PersonContact.objects.get(id=person.id)
    assert anonymized_person.name != person.name
    assert anonymized_person.user.username != person.user.username
