# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from decimal import Decimal

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from django.utils.translation import activate
from shoop.campaigns.models.campaigns import CatalogCampaign
from shoop.campaigns.models.catalog_filters import CategoryFilter
from shoop.campaigns.models.context_conditions import ContactGroupCondition
from shoop.core.models import Category
from shoop.testing.factories import create_product, get_default_customer_group
from shoop_tests.campaigns import initialize_test


@pytest.mark.django_db
def test_campaign_creation(rf):
    activate("en")
    request, shop, group = initialize_test(rf, False)
    cat = Category.objects.create(name="test")
    condition = ContactGroupCondition.objects.create()
    condition.contact_groups = request.customer.groups.all()
    condition.save()

    assert condition.values.first() == request.customer.groups.first()

    condition.values = request.customer.groups.all()
    condition.save()
    assert condition.values.first() == request.customer.groups.first()

    category_filter = CategoryFilter.objects.create()
    category_filter.categories.add(cat)
    category_filter.save()

    campaign = CatalogCampaign.objects.create(shop=shop, name="test", discount_amount_value=20, active=True)
    campaign.conditions.add(condition)
    campaign.filters.add(category_filter)
    campaign.save()


@pytest.mark.django_db
def test_condition_doesnt_match(rf):
    activate("en")
    request, shop, group = initialize_test(rf, False)
    condition = ContactGroupCondition.objects.create()
    condition.contact_groups = [get_default_customer_group()]
    condition.save()

    request.customer = None

    assert not condition.matches(request)


@pytest.mark.django_db
def test_condition_affects_price(rf):
    activate("en")
    request, shop, group = initialize_test(rf, False)
    cat = Category.objects.create(name="test")
    contact_condition = ContactGroupCondition.objects.create()
    contact_condition.contact_groups = request.customer.groups.all()
    contact_condition.save()

    campaign = CatalogCampaign.objects.create(shop=shop, name="test", discount_amount_value=20, active=True)
    campaign.conditions.add(contact_condition)
    campaign.save()

    price = shop.create_price

    product = create_product("Just-A-Product-Too", shop, default_price=199)

    assert product.get_price_info(request, quantity=1).price == price(179)


@pytest.mark.django_db
def test_filter_affects_price(rf):
    activate("en")
    request, shop, group = initialize_test(rf, False)
    cat = Category.objects.create(name="test")
    category_filter = CategoryFilter.objects.create()
    category_filter.categories.add(cat)
    category_filter.save()

    campaign = CatalogCampaign.objects.create(shop=shop, name="test", discount_amount_value=20, active=True)
    campaign.filters.add(category_filter)
    campaign.save()

    price = shop.create_price

    product = create_product("Just-A-Product-Too", shop, default_price=199)
    shop_product = product.get_shop_instance(shop)
    shop_product.categories.add(cat)
    shop_product.save()
    assert product.get_price_info(request, quantity=1).price == price(179)


@pytest.mark.django_db
def test_campaign_all_rules_must_match1(rf):
    activate("en")
    discount_amount = "20.53"
    original_price = "199.20"

    request, shop, group = initialize_test(rf, False)
    cat = Category.objects.create(name="test")
    rule1 = ContactGroupCondition.objects.create()
    rule1.contact_groups = request.customer.groups.all()
    rule1.save()

    rule2 = CategoryFilter.objects.create()
    rule2.categories.add(cat)
    rule2.save()

    campaign = CatalogCampaign.objects.create(shop=shop, name="test", discount_amount_value=discount_amount, active=True)
    campaign.conditions.add(rule1)
    campaign.filters.add(rule2)
    campaign.save()

    product = create_product("Just-A-Product-Too", shop, default_price=original_price)

    price = shop.create_price
    # price should not be discounted because the request.category is faulty
    assert product.get_price_info(request, quantity=1).price == price(original_price)

    shop_product = product.get_shop_instance(shop)
    shop_product.categories.add(cat)
    shop_product.save()
    # now the category is set, so both rules match, disconut should be given
    assert product.get_price_info(request, quantity=1).price == (price(original_price) - price(discount_amount))


@pytest.mark.django_db
def test_campaign_save_validation(rf):
    # Discount percentage, or Discount amount in shop currency
    request, shop, group = initialize_test(rf, False)
    with pytest.raises(ValidationError):
        campaign = CatalogCampaign.objects.create(shop=shop, name="test", discount_amount_value="20", discount_percentage="0.20")

    with pytest.raises(ValidationError):
        campaign = CatalogCampaign.objects.create(shop=shop, name="test")

@pytest.mark.django_db
def test_percentage_campaigns(rf):
    activate("en")
    discount_percentage = "0.14"
    original_price = "123.47"

    request, shop, group = initialize_test(rf, False)
    cat = Category.objects.create(name="test")
    rule1 = ContactGroupCondition.objects.create()
    rule1.contact_groups = request.customer.groups.all()
    rule1.save()

    rule2 = CategoryFilter.objects.create()
    rule2.categories.add(cat)
    rule2.save()
    campaign = CatalogCampaign.objects.create(shop=shop, name="test", discount_percentage=discount_percentage, active=True)
    campaign.conditions.add(rule1)
    campaign.filters.add(rule2)
    campaign.save()

    product = create_product("Just-A-Product-Too", shop, default_price=original_price)

    price = shop.create_price
    # price should not be discounted because the request.category is faulty
    assert product.get_price_info(request, quantity=1).price == price(original_price)

    shop_product = product.get_shop_instance(shop)
    shop_product.categories.add(cat)
    shop_product.save()
    # now the category is set, so both rules match, discount should be given
    discounted_price = price(original_price) - (price(original_price) * Decimal(campaign.discount_percentage))
    assert product.get_price_info(request, quantity=1).price == discounted_price


@pytest.mark.django_db
def test_only_best_price_affects(rf):
    activate("en")
    discount_amount = "20.53"
    original_price = "199.20"
    best_discount_amount = "40.00"

    request, shop, group = initialize_test(rf, False)
    cat = Category.objects.create(name="test")

    rule1, rule2 = create_condition_and_filter(cat, request)

    campaign = CatalogCampaign.objects.create(shop=shop, name="test", discount_amount_value=discount_amount, active=True)
    campaign.conditions.add(rule1)
    campaign.filters.add(rule2)
    campaign.save()

    rule3, rule4 = create_condition_and_filter(cat, request)

    campaign = CatalogCampaign.objects.create(shop=shop, name="test", discount_amount_value=best_discount_amount, active=True)
    campaign.conditions.add(rule3)
    campaign.filters.add(rule4)
    campaign.save()


    product = create_product("Just-A-Product-Too", shop, default_price=original_price)

    price = shop.create_price
    # price should not be discounted because the request.category is faulty
    assert product.get_price_info(request, quantity=1).price == price(original_price)

    shop_product = product.get_shop_instance(shop)
    shop_product.categories.add(cat)
    shop_product.save()
    # now the category is set, so both rules match, disconut should be given
    assert product.get_price_info(request, quantity=1).price == (price(original_price) - price(best_discount_amount))


@pytest.mark.django_db
def test_minimum_price_is_forced(rf):
    activate("en")
    discount_amount = "20.53"
    original_price = "199.20"
    allowed_minimum_price = "190.20"

    request, shop, group = initialize_test(rf, False)
    cat = Category.objects.create(name="test")
    rule1, rule2 = create_condition_and_filter(cat, request)
    campaign = CatalogCampaign.objects.create(shop=shop, name="test", discount_amount_value=discount_amount, active=True)
    campaign.conditions.add(rule1)
    campaign.filters.add(rule2)
    campaign.save()

    price = shop.create_price

    product = create_product("Just-A-Product-Too", shop, default_price=original_price)
    shop_product = product.get_shop_instance(shop)
    shop_product.minimum_price = price(allowed_minimum_price)
    shop_product.save()

    # price should not be discounted because the request.category is faulty
    assert product.get_price_info(request, quantity=1).price == price(original_price)

    shop_product.categories.add(cat)
    shop_product.save()
    # now the category is set, so both rules match, discount should be given
    assert product.get_price_info(request, quantity=1).price == shop_product.minimum_price


@pytest.mark.django_db
def test_price_cannot_be_under_zero(rf):

    activate("en")
    discount_amount = "200"
    original_price = "199.20"

    request, shop, group = initialize_test(rf, False)
    cat = Category.objects.create(name="test")
    rule1, rule2 = create_condition_and_filter(cat, request)
    campaign = CatalogCampaign.objects.create(shop=shop, name="test", discount_amount_value=discount_amount, active=True)
    campaign.conditions.add(rule1)
    campaign.filters.add(rule2)
    campaign.save()

    price = shop.create_price

    product = create_product("Just-A-Product-Too", shop, default_price=original_price)
    shop_product = product.get_shop_instance(shop)
    shop_product.categories.add(cat)
    shop_product.save()

    assert product.get_price_info(request, quantity=1).price == price("0")


def create_condition_and_filter(cat, request):
    rule1 = ContactGroupCondition.objects.create()
    rule1.contact_groups = request.customer.groups.all()
    rule1.save()
    rule2 = CategoryFilter.objects.create()
    rule2.categories.add(cat)
    rule2.save()
    return rule1, rule2


@pytest.mark.django_db
def test_start_end_dates(rf):
    activate("en")
    original_price = "180"
    discounted_price = "160"
    request, shop, group = initialize_test(rf, False)
    cat = Category.objects.create(name="test")
    rule1, rule2 = create_condition_and_filter(cat, request)

    campaign = CatalogCampaign.objects.create(shop=shop, name="test", discount_amount_value="20", active=True)
    campaign.conditions.add(rule1)
    campaign.save()
    price = shop.create_price

    product = create_product("Just-A-Product-Too", shop, default_price=original_price)

    today = now()

    # starts in future
    campaign.start_datetime = (today + datetime.timedelta(days=2))
    campaign.save()
    assert not campaign.is_available()
    assert product.get_price_info(request, quantity=1).price == price(original_price)

    # has already started
    campaign.start_datetime = (today - datetime.timedelta(days=2))
    campaign.save()
    assert product.get_price_info(request, quantity=1).price == price(discounted_price)

    # already ended
    campaign.end_datetime = (today - datetime.timedelta(days=1))
    campaign.save()
    assert not campaign.is_available()
    assert product.get_price_info(request, quantity=1).price == price(original_price)

    # not ended yet
    campaign.end_datetime = (today + datetime.timedelta(days=1))
    campaign.save()
    assert product.get_price_info(request, quantity=1).price == price(discounted_price)

    # no start datetime
    campaign.start_datetime = None
    campaign.save()
    assert product.get_price_info(request, quantity=1).price == price(discounted_price)

    # no start datetime but ended
    campaign.end_datetime = (today - datetime.timedelta(days=1))
    campaign.save()
    assert not campaign.is_available()
    assert product.get_price_info(request, quantity=1).price == price(original_price)


@pytest.mark.django_db
def test_availability(rf):
    activate("en")
    request, shop, group = initialize_test(rf, False)
    cat = Category.objects.create(name="test")
    rule1, rule2 = create_condition_and_filter(cat, request)

    campaign = CatalogCampaign.objects.create(shop=shop, name="test", discount_amount_value="20", active=False)
    campaign.conditions.add(rule1)
    campaign.save()

    assert not campaign.is_available()

