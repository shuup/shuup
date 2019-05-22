# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import uuid

import pytest
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from shuup import configuration
from shuup.core.models import CompanyContact, PersonContact, Shop, ShopStatus


@pytest.mark.django_db
def test_registration_person_multiple_shops(django_user_model, client):
    if "shuup.front.apps.registration" not in settings.INSTALLED_APPS:
        pytest.skip("shuup.front.apps.registration required in installed apps")

    shop1 = Shop.objects.create(identifier="shop1", status=ShopStatus.ENABLED, domain="shop1.shuup.com")
    shop2 = Shop.objects.create(identifier="shop2", status=ShopStatus.ENABLED, domain="shop2.shuup.com")

    with override_settings(
        SHUUP_REGISTRATION_REQUIRES_ACTIVATION=False,
        SHUUP_MANAGE_CONTACTS_PER_SHOP=True,
        SHUUP_ENABLE_MULTIPLE_SHOPS=True
    ):
        username = "u-%d" % uuid.uuid4().time
        email = "%s@shuup.local" % username

        client.post(reverse("shuup:registration_register"), data={
            "registration-username": username,
            "registration-email": email,
            "registration-password1": "password",
            "registration-password2": "password",
        }, HTTP_HOST="shop2.shuup.com")

        user = django_user_model.objects.get(username=username)
        contact = PersonContact.objects.get(user=user)
        assert contact.in_shop(shop2)
        assert contact.registered_in(shop2)
        assert not contact.in_shop(shop1)
        assert not contact.registered_in(shop1)


@pytest.mark.django_db
def test_registration_company_multiple_shops(django_user_model, client):
    if "shuup.front.apps.registration" not in settings.INSTALLED_APPS:
        pytest.skip("shuup.front.apps.registration required in installed apps")

    configuration.set(None, "allow_company_registration", True)
    configuration.set(None, "company_registration_requires_approval", False)

    shop1 = Shop.objects.create(identifier="shop1", status=ShopStatus.ENABLED, domain="shop1.shuup.com")
    shop2 = Shop.objects.create(identifier="shop2", status=ShopStatus.ENABLED, domain="shop2.shuup.com")
    username = "u-%d" % uuid.uuid4().time
    email = "%s@shuup.local" % username

    with override_settings(
        SHUUP_REGISTRATION_REQUIRES_ACTIVATION=False,
        SHUUP_MANAGE_CONTACTS_PER_SHOP=True,
        SHUUP_ENABLE_MULTIPLE_SHOPS=True
    ):
        url = reverse("shuup:registration_register_company")
        client.post(url, data={
            'registration_company-name': "Test company",
            'registration_company-name_ext': "test",
            'registration_company-tax_number': "12345",
            'registration_company-email': "test@example.com",
            'registration_company-phone': "123123",
            'registration_company-www': "",
            'registration_billing-street': "testa tesat",
            'registration_billing-street2': "",
            'registration_billing-postal_code': "12345",
            'registration_billing-city': "test test",
            'registration_billing-region': "",
            'registration_billing-region_code': "",
            'registration_billing-country': "FI",
            'registration_contact_person-first_name': "Test",
            'registration_contact_person-last_name': "Tester",
            'registration_contact_person-email': email,
            'registration_contact_person-phone': "123",
            'registration_user_account-username': username,
            'registration_user_account-password1': "password",
            'registration_user_account-password2': "password",
        }, HTTP_HOST="shop1.shuup.com")
        user = django_user_model.objects.get(username=username)
        contact = PersonContact.objects.get(user=user)
        company = CompanyContact.objects.get(members__in=[contact])

        assert contact.in_shop(shop1)
        assert company.in_shop(shop1)
        assert contact.in_shop(shop1, only_registration=True)
        assert company.in_shop(shop1, only_registration=True)
        assert contact.registered_in(shop1)
        assert company.registered_in(shop1)

        assert not contact.in_shop(shop2)
        assert not company.in_shop(shop2)
        assert not contact.in_shop(shop2, only_registration=True)
        assert not company.in_shop(shop2, only_registration=True)
        assert not contact.registered_in(shop2)
        assert not company.registered_in(shop2)
