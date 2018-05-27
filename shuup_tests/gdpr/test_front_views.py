# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import pytest
from django.core.urlresolvers import reverse
from django.utils.translation import activate

from shuup.testing import factories
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

    response = client.post(reverse("shuup:gdpr_anonymize_account"))
    assert response.status_code == 302
    assert response.url.endswith(reverse("shuup:index"))
