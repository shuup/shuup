# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.test import override_settings
from django.test.client import RequestFactory

from shuup.campaigns.models.campaigns import CatalogCampaign
from shuup.campaigns.models.context_conditions import ContactCondition, ContactGroupCondition
from shuup.campaigns.models.product_effects import ProductDiscountAmount
from shuup.core.models import AnonymousContact
from shuup.testing.factories import create_product, create_random_person, get_default_customer_group, get_shop
from shuup.testing.utils import apply_request_middleware


def get_request_for_contact_tests(rf):
    request = rf.get("/")
    request.shop = get_shop(prices_include_tax=True)
    apply_request_middleware(request)
    return request


def create_random_product_and_campaign(shop, conditions, original_price_value, discount_value):
    campaign = CatalogCampaign.objects.create(shop=shop, name="test", active=True)
    ProductDiscountAmount.objects.create(discount_amount=discount_value, campaign=campaign)
    for condition in conditions:
        campaign.conditions.add(condition)
    assert campaign.is_available()

    product = create_product("Some crazy product", shop, default_price=original_price_value)
    return product


def assert_product_price_value_with_customer(request, customer, product, price_value):
    request.customer = customer
    price = request.shop.create_price
    assert product.get_price_info(request, quantity=1).price == price(price_value)


@pytest.mark.django_db
@override_settings(SHUUP_DISCOUNT_MODULES=["customer_group_discount", "catalog_campaigns"])
def test_context_contact_group_condition():
    rf = RequestFactory()
    original_price_value, discount_value = 123, 15
    request = get_request_for_contact_tests(rf)
    customer = create_random_person()
    default_group = get_default_customer_group()
    customer.groups.add(default_group)
    request.customer = customer

    condition = ContactGroupCondition.objects.create()
    condition.contact_groups.add(default_group)
    product = create_random_product_and_campaign(request.shop, [condition], original_price_value, discount_value)

    discounted_value = original_price_value - discount_value
    assert_product_price_value_with_customer(request, customer, product, discounted_value)

    request.customer.groups.clear()
    assert_product_price_value_with_customer(request, customer, product, original_price_value)


@pytest.mark.django_db
@override_settings(SHUUP_DISCOUNT_MODULES=["customer_group_discount", "catalog_campaigns"])
def test_group_condition_with_anonymous_contact():
    rf = RequestFactory()
    original_price_value, discount_value = 6, 4
    request = get_request_for_contact_tests(rf)
    assert isinstance(request.customer, AnonymousContact)
    condition = ContactGroupCondition.objects.create()
    condition.contact_groups.add(request.customer.groups.first())
    product = create_random_product_and_campaign(request.shop, [condition], original_price_value, discount_value)

    discounted_value = original_price_value - discount_value
    assert_product_price_value_with_customer(request, request.customer, product, discounted_value)


@pytest.mark.django_db
@override_settings(SHUUP_DISCOUNT_MODULES=["customer_group_discount", "catalog_campaigns"])
def test_context_contact_condition():
    rf = RequestFactory()
    original_price_value, discount_value = 2, 1
    request = get_request_for_contact_tests(rf)
    random_person = create_random_person()
    condition = ContactCondition.objects.create()
    condition.contacts.add(random_person)
    product = create_random_product_and_campaign(request.shop, [condition], original_price_value, discount_value)

    # random_person should get this campaign
    discounted_value = original_price_value - discount_value
    assert_product_price_value_with_customer(request, random_person, product, discounted_value)

    another_random_person = create_random_person()
    # another random person shouldn't
    assert_product_price_value_with_customer(request, another_random_person, product, original_price_value)

    # Add another random person for the rule and see if he get's the discount
    condition.contacts.add(another_random_person)
    assert_product_price_value_with_customer(request, another_random_person, product, discounted_value)

    # Remove random person from rule and see the discount disappear
    condition.contacts.remove(random_person)
    condition.save()
    assert_product_price_value_with_customer(request, random_person, product, original_price_value)
