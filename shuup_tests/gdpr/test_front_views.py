# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.contrib.auth.models import AnonymousUser
from django.utils.translation import activate

from shuup.core.models import PersonContact, Shop
from shuup.gdpr.models import GDPRSettings
from shuup.gdpr.utils import (
    create_initial_required_cookie_category,
    ensure_gdpr_privacy_policy,
    is_documents_consent_in_sync,
)
from shuup.gdpr.views import GDPRCookieConsentView, GDPRPolicyConsentView
from shuup.simple_cms.models import Page
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import reverse
from shuup_tests.utils import SmartClient


@pytest.mark.django_db
def test_serialize_data():
    """
    Test contact dashboard views
    """
    activate("en")
    shop = factories.get_default_shop()

    customer = factories.create_random_person("en")
    user = factories.create_random_user("en")
    user.set_password("1234")
    user.save()
    customer.user = user
    customer.default_billing_address = factories.create_random_address()
    customer.default_shipping_address = factories.create_random_address()
    customer.save()

    company = factories.create_random_company()
    company.default_billing_address = factories.create_random_address()
    company.default_shipping_address = factories.create_random_address()
    company.save()
    company.members.add(customer)

    product = factories.create_product("p1", shop, factories.get_default_supplier())
    for basket_customer in [customer, company]:
        [factories.create_random_order(basket_customer, [product]) for order in range(3)]

    client = SmartClient()
    client.login(username=user.username, password="1234")

    response = client.get(reverse("shuup:gdpr_customer_dashboard"))
    assert response.status_code == 200
    assert "My Data" in response.content.decode("utf-8")

    response = client.post(reverse("shuup:gdpr_download_data"))
    assert response._headers["content-disposition"][0] == "Content-Disposition"
    assert response.status_code == 200

    from shuup.gdpr.models import GDPR_ANONYMIZE_TASK_TYPE_IDENTIFIER
    from shuup.tasks.models import Task, TaskType

    response = client.post(reverse("shuup:gdpr_anonymize_account"))
    assert response.status_code == 302
    assert response.url.endswith(reverse("shuup:index"))
    task_type = TaskType.objects.get(identifier=GDPR_ANONYMIZE_TASK_TYPE_IDENTIFIER, shop=shop)
    assert Task.objects.get(type=task_type, shop=shop)

    user.refresh_from_db()
    assert user.is_active is False

    refreshed_customer = PersonContact.objects.get(id=customer.id)
    assert refreshed_customer.is_active is False
    assert refreshed_customer.name == customer.name  # nothing changed yet


@pytest.mark.django_db
@pytest.mark.parametrize("language", ["fi", "en"])
def test_cookie_consent_view(rf, language):
    activate(language)
    shop = factories.get_default_shop()
    page = ensure_gdpr_privacy_policy(shop)
    user = factories.create_random_user("en")

    gdpr_settings = GDPRSettings.get_for_shop(shop)
    gdpr_settings.enabled = True
    gdpr_settings.save()

    create_initial_required_cookie_category(shop)
    view = GDPRCookieConsentView.as_view()
    request = apply_request_middleware(rf.post("/"), shop=shop, user=user)
    response = view(request, pk=None)
    assert response.status_code == 302

    modified = page.modified_on
    new_page = ensure_gdpr_privacy_policy(shop)
    assert new_page.pk == page.pk
    assert modified == new_page.modified_on  # no update done.

    new_page = ensure_gdpr_privacy_policy(shop, force_update=True)
    assert modified < new_page.modified_on  # no update done.


@pytest.mark.django_db()
@pytest.mark.parametrize("language", ["fi", "en"])
def test_policy_consent_view(rf, language):
    activate(language)
    shop = factories.get_default_shop()
    user = factories.create_random_user("en")

    page = ensure_gdpr_privacy_policy(shop)

    view = GDPRPolicyConsentView.as_view()

    # try without user
    request = apply_request_middleware(rf.post("/"), shop=shop)
    response = view(request, page_id=page.id)
    assert response.status_code == 404

    # try with anonymous user
    anonymous_user = AnonymousUser()
    request = apply_request_middleware(rf.post("/"), shop=shop, user=anonymous_user)
    response = view(request, page_id=page.id)
    assert response.status_code == 404

    # try without correct page
    incorrect_shop = Shop.objects.create(name="testing", public_name="testing..")
    incorrect_page = Page.objects.create(shop=incorrect_shop)
    request = apply_request_middleware(rf.post("/"), shop=shop, user=user)
    response = view(request, page_id=incorrect_page.id)
    assert response.status_code == 404

    assert is_documents_consent_in_sync(shop, user)  # returns true because no settings set
    request = apply_request_middleware(rf.post("/"), shop=shop, user=user)
    response = view(request, page_id=page.id)
    assert response.status_code == 404  # gdpr settings not enabled

    gdpr_settings = GDPRSettings.get_for_shop(shop)
    gdpr_settings.enabled = True
    gdpr_settings.privacy_policy = page
    gdpr_settings.save()

    request = apply_request_middleware(rf.post("/"), shop=shop, user=user)
    response = view(request, page_id=page.id)
    assert response.status_code == 302  # all good!

    assert is_documents_consent_in_sync(shop, user)
