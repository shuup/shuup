# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import datetime
import decimal

import pytest

from django.core.management import call_command

from shuup.campaigns.models import CatalogCampaign
from shuup.campaigns.models.catalog_filters import (
    CategoryFilter, ProductFilter
)
from shuup.campaigns.models.context_conditions import (
    ContactCondition, ContactGroupCondition, HourCondition
)
from shuup.campaigns.models.product_effects import (
    ProductDiscountAmount, ProductDiscountPercentage
)
from shuup.discounts.models import Discount, HappyHour, TimeRange
from shuup.testing import factories


@pytest.mark.django_db
def test_catalog_campaign_sync():
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()
    default_price = 100
    product1 = factories.create_product("test1", shop=shop, supplier=supplier, default_price=default_price)
    product2 = factories.create_product("test2", shop=shop, supplier=supplier, default_price=default_price)
    product3 = factories.create_product("test3", shop=shop, supplier=supplier, default_price=default_price)
    category = factories.get_default_category()
    shop_product = product1.get_shop_instance(shop)
    shop_product.primary_category = category
    shop_product.save()
    shop_product.categories.add(category)

    contact1 = factories.create_random_person()

    contact2 = factories.create_random_person()
    contact_group = factories.get_default_customer_group()
    contact2.groups.add(contact_group)

    happy_hour1_weekdays = "0,1"  # Mon, Tue
    happy_hour1_start = datetime.time(21)
    happy_hour1_end = datetime.time(3)
    happy_hour1_condition = HourCondition.objects.create(
        days=happy_hour1_weekdays, hour_start=happy_hour1_start, hour_end=happy_hour1_end)

    happy_hour2_weekdays = "2,6"  # Wed, Sun
    happy_hour2_start = datetime.time(14)
    happy_hour2_end = datetime.time(16)
    happy_hour2_condition = HourCondition.objects.create(
        days=happy_hour2_weekdays, hour_start=happy_hour2_start, hour_end=happy_hour2_end)

    discount_amount_value = 50
    discount_percentage = decimal.Decimal("0.35")
    _create_catalog_campaign_for_products(
        shop, [product1], discount_amount_value, happy_hour1_condition)
    _create_catalog_campaign_for_products(
        shop, [product2, product3], discount_amount_value)
    _create_catalog_campaign_for_category(
        shop, category, discount_percentage)
    _create_catalog_campaign_for_contact(
        shop, product1, contact1, discount_amount_value)
    _create_catalog_campaign_for_contact_group(
        shop, [product1, product2, product3], contact_group, discount_percentage, happy_hour2_condition)

    call_command("import_catalog_campaigns", *[], **{})

    # From first campaign we should get 1 discount with happy hour
    # From second campaign we should get 2 discounts
    # From third campaign we should get 1 discount
    # From fourth campaign we should get also 1 discount
    # From last campaign we should get 3 discounts with happy hour
    assert Discount.objects.count() == 8

    # There should be 2 happy hours in total
    assert HappyHour.objects.count() == 2

    # From first happy hour there should be 4 ranges
    # Mon 21-23, Tue 0-3, Tue 21-23, Wed 0-3
    # From second happy hour there should be 2 ranges
    # Wed 14-16 and Sun 14-16
    assert TimeRange.objects.count() == 6

    # Let's go through all our 8 discounts to make sure all is good
    first_discount = Discount.objects.filter(
        product=product1, category__isnull=True, contact__isnull=True, contact_group__isnull=True).first()
    assert first_discount.happy_hours.count() == 1
    assert first_discount.discount_amount_value == discount_amount_value

    second_discount = Discount.objects.filter(
        product=product2, category__isnull=True, contact__isnull=True, contact_group__isnull=True).first()
    assert second_discount.happy_hours.count() == 0
    assert second_discount.discount_amount_value == discount_amount_value

    third_discount = Discount.objects.filter(
        product=product3, category__isnull=True, contact__isnull=True, contact_group__isnull=True).first()
    assert third_discount.happy_hours.count() == 0
    assert third_discount.discount_amount_value == discount_amount_value

    category_discount = Discount.objects.filter(
        product__isnull=True, category=category, contact__isnull=True, contact_group__isnull=True).first()
    assert category_discount.happy_hours.count() == 0
    assert category_discount.discount_percentage == discount_percentage

    contact_discount = Discount.objects.filter(
        product=product1, category__isnull=True, contact=contact1, contact_group__isnull=True).first()
    assert contact_discount.discount_amount_value == discount_amount_value

    product1_contact_group_discount = Discount.objects.filter(
        product=product1, category__isnull=True, contact__isnull=True, contact_group=contact_group).first()
    assert product1_contact_group_discount.happy_hours.count() == 1
    assert product1_contact_group_discount.discount_percentage == discount_percentage

    product2_contact_group_discount = Discount.objects.filter(
        product=product2, category__isnull=True, contact__isnull=True, contact_group=contact_group).first()
    assert product2_contact_group_discount.happy_hours.count() == 1
    assert product2_contact_group_discount.discount_percentage == discount_percentage

    product3_contact_group_discount = Discount.objects.filter(
        product=product3, category__isnull=True, contact__isnull=True, contact_group=contact_group).first()
    assert product3_contact_group_discount.happy_hours.count() == 1
    assert product3_contact_group_discount.discount_percentage == discount_percentage


def _create_catalog_campaign_for_products(shop, products, discount_amount_value, happy_hour_condition=None):
    campaign = CatalogCampaign.objects.create(active=True, shop=shop)
    product_filter = ProductFilter.objects.create()
    for product in products:
        product_filter.products.add(product)
    campaign.filters.add(product_filter)
    if happy_hour_condition:
        campaign.conditions.add(happy_hour_condition)

    ProductDiscountAmount.objects.create(campaign=campaign, discount_amount=discount_amount_value)
    return campaign


def _create_catalog_campaign_for_category(shop, category, discount_percentage):
    campaign = CatalogCampaign.objects.create(active=True, shop=shop)
    category_filter = CategoryFilter.objects.create()
    category_filter.categories.add(category)
    campaign.filters.add(category_filter)

    ProductDiscountPercentage.objects.create(campaign=campaign, discount_percentage=discount_percentage)
    return campaign


def _create_catalog_campaign_for_contact(shop, product, contact, discount_amount_value):
    campaign = CatalogCampaign.objects.create(active=True, shop=shop)
    product_filter = ProductFilter.objects.create()
    product_filter.products.add(product)
    campaign.filters.add(product_filter)

    contact_condition = ContactCondition.objects.create()
    contact_condition.contacts.add(contact)
    campaign.conditions.add(contact_condition)

    ProductDiscountAmount.objects.create(campaign=campaign, discount_amount=discount_amount_value)
    return campaign


def _create_catalog_campaign_for_contact_group(shop, products, contact_group, discount_percentage, happy_hour_condition):
    campaign = CatalogCampaign.objects.create(active=True, shop=shop)
    product_filter = ProductFilter.objects.create()
    for product in products:
        product_filter.products.add(product)
    campaign.filters.add(product_filter)

    contact_group_condition = ContactGroupCondition.objects.create()
    contact_group_condition.contact_groups.add(contact_group)
    campaign.conditions.add(contact_group_condition)
    campaign.conditions.add(happy_hour_condition)

    ProductDiscountPercentage.objects.create(campaign=campaign, discount_percentage=discount_percentage)
    return campaign
