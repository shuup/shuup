# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.utils.translation import activate

from shuup.campaigns.models.basket_conditions import ContactBasketCondition, ContactGroupBasketCondition
from shuup.campaigns.models.basket_effects import BasketDiscountAmount
from shuup.campaigns.models.campaigns import BasketCampaign
from shuup.core.models import AnonymousContact, Shop
from shuup.front.basket import get_basket
from shuup.testing.factories import (
    create_product,
    create_random_person,
    get_default_customer_group,
    get_default_supplier,
    get_payment_method,
    get_shipping_method,
    get_shop,
)
from shuup.testing.utils import apply_request_middleware


def get_request_for_contact_tests(rf):
    activate("en")
    request = rf.get("/")
    request.shop = get_shop(prices_include_tax=True)
    get_payment_method(request.shop)
    apply_request_middleware(request)
    return request


def create_basket_and_campaign(request, conditions, product_price_value, campaign_discount_value):
    product = create_product(
        "Some crazy product", request.shop, get_default_supplier(), default_price=product_price_value
    )
    basket = get_basket(request)
    basket.customer = request.customer
    supplier = get_default_supplier()
    basket.add_product(supplier=supplier, shop=request.shop, product=product, quantity=1)
    basket.shipping_method = get_shipping_method(shop=request.shop)

    original_line_count = len(basket.get_final_lines())
    assert original_line_count == 2
    assert basket.product_count == 1
    original_price = basket.total_price

    campaign = BasketCampaign.objects.create(shop=request.shop, name="test", public_name="test", active=True)
    BasketDiscountAmount.objects.create(campaign=campaign, discount_amount=campaign_discount_value)

    for condition in conditions:
        campaign.conditions.add(condition)
    assert campaign.is_available()

    return basket, original_line_count, original_price


def assert_discounted_basket(basket, original_line_count, original_price, campaign_discount_value):
    basket.uncache()
    price = basket.shop.create_price
    assert len(basket.get_final_lines()) == original_line_count + 1
    assert basket.total_price == original_price - price(campaign_discount_value)


def assert_non_discounted_basket(basket, original_line_count, original_price):
    basket.uncache()
    assert len(basket.get_final_lines()) == original_line_count
    assert basket.total_price == original_price


@pytest.mark.django_db
def test_basket_contact_group_condition(rf):
    product_price_value, campaign_discount_value = 123, 15
    request = get_request_for_contact_tests(rf)
    customer = create_random_person()
    default_group = get_default_customer_group()
    customer.groups.add(default_group)
    request.customer = customer

    condition = ContactGroupBasketCondition.objects.create()
    condition.contact_groups.add(default_group)
    basket, original_line_count, original_price = create_basket_and_campaign(
        request, [condition], product_price_value, campaign_discount_value
    )

    assert basket.customer == customer
    assert_discounted_basket(basket, original_line_count, original_price, campaign_discount_value)

    customer.groups.remove(default_group)
    assert_non_discounted_basket(basket, original_line_count, original_price)


@pytest.mark.django_db
def test_group_basket_condition_with_anonymous_contact(rf):
    product_price_value, campaign_discount_value = 6, 4
    request = get_request_for_contact_tests(rf)
    assert isinstance(request.customer, AnonymousContact)
    condition = ContactGroupBasketCondition.objects.create()
    condition.contact_groups.add(request.customer.groups.first())

    basket, original_line_count, original_price = create_basket_and_campaign(
        request, [condition], product_price_value, campaign_discount_value
    )

    assert isinstance(basket.customer, AnonymousContact)
    assert_discounted_basket(basket, original_line_count, original_price, campaign_discount_value)


@pytest.mark.django_db
def test_contact_group_basket_condition_with_none(rf):
    request = apply_request_middleware(rf.get("/"))
    request.shop = Shop()
    basket = get_basket(request)
    condition = ContactGroupBasketCondition.objects.create()
    result = condition.matches(basket)  # Should not raise any errors
    assert result is False


@pytest.mark.django_db
def test_basket_contact_condition(rf):
    product_price_value, campaign_discount_value = 2, 1
    request = get_request_for_contact_tests(rf)
    random_person = create_random_person()
    request.customer = random_person
    condition = ContactBasketCondition.objects.create()
    condition.contacts.add(random_person)
    basket, original_line_count, original_price = create_basket_and_campaign(
        request, [condition], product_price_value, campaign_discount_value
    )

    # random_person should get this campaign
    assert basket.customer == random_person
    assert_discounted_basket(basket, original_line_count, original_price, campaign_discount_value)

    another_random_person = create_random_person()
    basket.customer = another_random_person
    # another random person shouldn't
    assert_non_discounted_basket(basket, original_line_count, original_price)

    # Add another random person for the rule and see if he get's the discount
    condition.contacts.add(another_random_person)
    condition.save()
    assert_discounted_basket(basket, original_line_count, original_price, campaign_discount_value)
    assert basket.customer == another_random_person

    # Remove random person from rule and see the discount disappear
    condition.contacts.remove(random_person)
    condition.save()
    basket.customer = random_person
    assert_non_discounted_basket(basket, original_line_count, original_price)
    assert basket.customer == random_person
