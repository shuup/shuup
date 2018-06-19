# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import pytest
from django.core.urlresolvers import reverse
from django.utils.translation import activate

from shuup.core.models import PersonContact
from shuup.gdpr.models import GDPRCookieCategory
from shuup.gdpr.utils import ensure_gdpr_privacy_policy, get_cookie_consent_data, \
    create_initial_required_cookie_category, is_documents_consent_in_sync
from shuup.gdpr.views import GDPRCookieConsentView
from shuup.simple_cms.models import Page, PageType
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware
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

    from shuup.tasks.models import Task, TaskType
    from shuup.gdpr.models import GDPR_ANONYMIZE_TASK_TYPE_IDENTIFIER
    response = client.post(reverse("shuup:gdpr_anonymize_account"))
    assert response.status_code == 302
    assert response.url.endswith(reverse("shuup:index"))
    task_type = TaskType.objects.get(identifier=GDPR_ANONYMIZE_TASK_TYPE_IDENTIFIER, shop=shop)
    assert Task.objects.get(type=task_type, shop=shop)

    user.refresh_from_db()
    assert user.is_active is False

    refreshed_customer = PersonContact.objects.get(id=customer.id)
    assert refreshed_customer.is_active is False
    assert refreshed_customer.name == customer.name     # nothing changed yet


@pytest.mark.django_db
@pytest.mark.parametrize("language", ["fi", "en"])
def test_cookie_consent_view(rf, language):
    activate(language)
    shop = factories.get_default_shop()
    page = ensure_gdpr_privacy_policy(shop)
    user = factories.create_random_user("en")

    create_initial_required_cookie_category(shop)
    view = GDPRCookieConsentView.as_view()
    request = apply_request_middleware(rf.post("/"), shop=shop, user=user)
    response = view(request, pk=None)
    assert response.status_code == 302

    modified = page.modified_on
    new_page = ensure_gdpr_privacy_policy(shop)
    assert modified == new_page.modified_on  # no update done.

    new_page = ensure_gdpr_privacy_policy(shop, force_update=True)
    assert modified < new_page.modified_on  # no update done.
