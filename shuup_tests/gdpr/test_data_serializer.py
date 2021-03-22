# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.utils.translation import activate
from uuid import uuid4

from shuup.core.models import Basket
from shuup.front.models import StoredBasket
from shuup.gdpr.serializers import GDPRPersonContactSerializer
from shuup.testing import factories


@pytest.mark.django_db
def test_serialize_data():
    """
    Test that contact data is serialized
    """
    activate("en")
    shop = factories.get_default_shop()

    customer = factories.create_random_person("en")
    user = factories.create_random_user("en")
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

    orders = []
    core_baskets = []
    front_baskets = []

    for basket_customer in [customer, company]:
        orders.extend([factories.create_random_order(basket_customer, [product]) for order in range(3)])

        front_baskets.append(
            StoredBasket.objects.create(
                key=uuid4().hex,
                shop=shop,
                customer=basket_customer,
                orderer=customer,
                creator=customer.user,
                currency=shop.currency,
                data={"items": []},
                prices_include_tax=shop.prices_include_tax,
            )
        )
        core_baskets.append(
            Basket.objects.create(
                key=uuid4().hex,
                shop=shop,
                customer=basket_customer,
                orderer=customer,
                creator=customer.user,
                currency=shop.currency,
                data={"items": []},
                prices_include_tax=shop.prices_include_tax,
            )
        )

    person_data = GDPRPersonContactSerializer(customer).data
    assert person_data["name"] == customer.name
    assert person_data["phone"] == customer.phone
    assert person_data["default_billing_address"]["street"] == customer.default_billing_address.street
    assert person_data["default_shipping_address"]["street"] == customer.default_shipping_address.street
    assert person_data["user"]["id"] == customer.user.id
    assert person_data["user"]["username"] == customer.user.username
    assert person_data["company_memberships"][0]["name"] == company.name
    assert person_data["company_memberships"][0]["id"] == company.id
    assert len(person_data["orders"]) == 3
    assert len(person_data["saved_baskets"]) == 1
    assert len(person_data["baskets"]) == 1
