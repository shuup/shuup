# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.contrib.auth import get_user_model
from django.utils.translation import activate
from uuid import uuid4

from shuup.core.models import Basket, CompanyContact, Order, PersonContact
from shuup.front.models import StoredBasket
from shuup.gdpr.anonymizer import Anonymizer
from shuup.testing import factories


@pytest.mark.django_db
def test_anonymize_contact():
    """
    Test that contact are anonymized
    """
    activate("en")
    shop = factories.get_default_shop()
    anonymizer = Anonymizer()

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

    anonymized_person = PersonContact.objects.get(id=customer.id)
    anonymizer._anonymize_person(anonymized_person)
    anonymized_person.refresh_from_db()
    assert anonymized_person.first_name != customer.first_name
    assert anonymized_person.last_name != customer.last_name
    assert anonymized_person.email != customer.email
    assert anonymized_person.phone != customer.phone
    assert anonymized_person.default_billing_address.street != customer.default_billing_address.street
    assert anonymized_person.default_billing_address.city != customer.default_billing_address.city

    anonymized_company = CompanyContact.objects.get(id=company.id)
    anonymizer._anonymize_company(anonymized_company)
    anonymized_company.refresh_from_db()
    assert anonymized_company.tax_number != company.tax_number
    assert anonymized_company.email != company.email
    assert anonymized_company.phone != company.phone
    assert anonymized_company.default_billing_address.street != company.default_billing_address.street
    assert anonymized_company.default_billing_address.city != company.default_billing_address.city

    for created_order in orders:
        order = Order.objects.get(id=created_order.id)
        assert order.phone != created_order.phone
        assert order.ip_address != created_order.ip_address
        assert order.shipping_address.street != created_order.shipping_address.street
        assert order.billing_address.street != created_order.billing_address.street

    for front_basket in front_baskets:
        stored_basket = StoredBasket.objects.get(id=front_basket.id)
        assert stored_basket.data is None

    for core_basket in core_baskets:
        basket = Basket.objects.get(id=core_basket.id)
        assert basket.data is None

    anonymized_user = get_user_model().objects.get(id=user.id)
    anonymizer._anonymize_user(anonymized_user)
    anonymized_user.refresh_from_db()
    assert user.username != anonymized_user.username
    assert user.first_name != anonymized_user.first_name
    assert user.last_name != anonymized_user.last_name


@pytest.mark.django_db
def test_anonymize():
    """
    Test that contact are anonymized
    """
    activate("en")
    shop = factories.get_default_shop()
    anonymizer = Anonymizer()

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

    orders.extend([factories.create_random_order(customer, [product]) for order in range(3)])

    front_baskets.append(
        StoredBasket.objects.create(
            key=uuid4().hex,
            shop=shop,
            customer=customer,
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
            customer=customer,
            orderer=customer,
            creator=customer.user,
            currency=shop.currency,
            data={"items": []},
            prices_include_tax=shop.prices_include_tax,
        )
    )

    user = get_user_model().objects.get(id=user.id)
    anonymized_person = PersonContact.objects.get(id=customer.id)

    anonymizer.anonymize(shop, anonymized_person, user=anonymized_person.user)
    anonymized_person.refresh_from_db()
    assert anonymized_person.first_name != customer.first_name
    assert anonymized_person.last_name != customer.last_name
    assert anonymized_person.email != customer.email
    assert anonymized_person.phone != customer.phone
    assert anonymized_person.default_billing_address.street != customer.default_billing_address.street
    assert anonymized_person.default_billing_address.city != customer.default_billing_address.city

    for created_order in orders:
        order = Order.objects.get(id=created_order.id)
        assert order.phone != created_order.phone
        assert order.ip_address != created_order.ip_address
        assert order.shipping_address.street != created_order.shipping_address.street
        assert order.billing_address.street != created_order.billing_address.street

    for front_basket in front_baskets:
        stored_basket = StoredBasket.objects.get(id=front_basket.id)
        assert stored_basket.data is None

    for core_basket in core_baskets:
        basket = Basket.objects.get(id=core_basket.id)
        assert basket.data is None

    anonymized_user = customer.user
    anonymized_user.refresh_from_db()
    assert user.username != anonymized_user.username
    assert user.first_name != anonymized_user.first_name
    assert user.last_name != anonymized_user.last_name
