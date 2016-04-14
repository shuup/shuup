# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import pytest

from django.core.exceptions import ValidationError

from shoop.campaigns.signal_handlers import (
    _get_total_sales, _assign_to_group_based_on_sales, update_customers_groups
)
from shoop.campaigns.models import ContactGroupSalesRange
from shoop.core.models import AnonymousContact, ContactGroup, Payment
from shoop.testing.factories import (
    create_order_with_product, create_product, create_random_company,
    create_random_person, get_default_shop, get_default_supplier
)


@pytest.mark.django_db
@pytest.mark.parametrize("get_contact", [
    AnonymousContact,
    create_random_company,
    create_random_person
])
def test_sales_ranges_for_default_groups(get_contact):
    shop = get_default_shop()
    group = get_contact().get_default_group()

    with pytest.raises(ValidationError):
        ContactGroupSalesRange.objects.create(group=group, shop=shop, min_value=1, max_value=100)


def create_fully_paid_order(shop, customer, supplier, product_sku, price_value):
    product = create_product(product_sku, shop=shop, supplier=supplier, default_price=price_value)
    order = create_order_with_product(
        product=product, supplier=supplier, quantity=1, taxless_base_unit_price=price_value, shop=get_default_shop())
    order.customer = customer
    order.save()
    order.cache_prices()
    return order.create_payment(order.taxful_total_price)


def create_sales_level(group, shop, minimum, maximum):
    contact_group, _ = ContactGroup.objects.get_or_create(identifier=group)
    return ContactGroupSalesRange.objects.create(
        group=contact_group, shop=shop, min_value=minimum, max_value=maximum)


@pytest.mark.django_db
def test_sales_ranges_basic():
    shop = get_default_shop()
    supplier = get_default_supplier()
    person = create_random_person()
    initial_group_count = person.groups.count()
    sales_ranges = [
        ("silver", 0, 50),
        ("gold", 50, 100),
        ("diamond", 100, 1000)
    ]
    for identifier, min, max in sales_ranges:
        create_sales_level(identifier, shop, min, max)

    payment = create_fully_paid_order(shop, person, supplier, "sku1", 10)
    assert _get_total_sales(shop, person) == 10
    update_customers_groups(Payment, payment)
    assert person.groups.count() == (initial_group_count + 1)
    assert bool([group for group in person.groups.all() if group.identifier == "silver"])

    payment = create_fully_paid_order(shop, person, supplier, "sku2", 50)
    assert _get_total_sales(shop, person) == 60
    update_customers_groups(Payment, payment)
    assert person.groups.count() == (initial_group_count + 1)
    assert bool([group for group in person.groups.all() if group.identifier == "gold"])

    payment = create_fully_paid_order(shop, person, supplier, "sku3", 200)
    assert _get_total_sales(shop, person) == 260
    update_customers_groups(Payment, payment)
    assert person.groups.count() == (initial_group_count + 1)
    assert bool([group for group in person.groups.all() if group.identifier == "diamond"])


@pytest.mark.django_db
def test_max_amount_none():
    shop = get_default_shop()
    supplier = get_default_supplier()
    person = create_random_person()
    initial_group_count = person.groups.count()
    sales_ranges = [
        ("silver", 0, 50),
        ("gold", 50, None),
        ("diamond", 100, None)
    ]
    for identifier, min, max in sales_ranges:
        create_sales_level(identifier, shop, min, max)

    payment = create_fully_paid_order(shop, person, supplier, "sku3", 200)
    assert _get_total_sales(shop, person) == 200
    update_customers_groups(Payment, payment)
    assert person.groups.count() == (initial_group_count + 2)
    assert bool([group for group in person.groups.all() if group.identifier == "gold"])
    assert bool([group for group in person.groups.all() if group.identifier == "diamond"])


@pytest.mark.django_db
def test_sales_between_ranges():
    shop = get_default_shop()
    supplier = get_default_supplier()
    person = create_random_person()
    initial_group_count = person.groups.count()
    sales_ranges = [
        ("silver", 0, 50),
        ("diamond", 100, None)
    ]
    for identifier, min, max in sales_ranges:
        create_sales_level(identifier, shop, min, max)

    payment = create_fully_paid_order(shop, person, supplier, "sku1", 10)
    assert _get_total_sales(shop, person) == 10
    update_customers_groups(Payment, payment)
    assert person.groups.count() == (initial_group_count + 1)
    assert bool([group for group in person.groups.all() if group.identifier == "silver"])

    payment = create_fully_paid_order(shop, person, supplier, "sku2", 50)
    assert _get_total_sales(shop, person) == 60
    update_customers_groups(Payment, payment)
    assert person.groups.count() == initial_group_count
    assert not bool([group for group in person.groups.all() if group.identifier in ["silver", "gold", "diamond"]])

    payment = create_fully_paid_order(shop, person, supplier, "sku3", 200)
    assert _get_total_sales(shop, person) == 260
    update_customers_groups(Payment, payment)
    assert person.groups.count() == (initial_group_count + 1)
    assert bool([group for group in person.groups.all() if group.identifier == "diamond"])


@pytest.mark.django_db
def test_min_amount_is_not_included():
    shop = get_default_shop()
    supplier = get_default_supplier()
    person = create_random_person()
    initial_group_count = person.groups.count()
    sales_ranges = [
        ("silver", 0, 50),
        ("gold", 50, 100),
        ("diamond", 100, 1000)
    ]
    for identifier, min, max in sales_ranges:
        create_sales_level(identifier, shop, min, max)

    payment = create_fully_paid_order(shop, person, supplier, "sku1", 50)
    assert _get_total_sales(shop, person) == 50
    update_customers_groups(Payment, payment)
    assert person.groups.count() == (initial_group_count + 1)
    assert bool([group for group in person.groups.all() if group.identifier == "gold"])
    assert not bool([group for group in person.groups.all() if group.identifier in ["silver", "diamond"]])

    payment = create_fully_paid_order(shop, person, supplier, "sku2", 50)
    assert _get_total_sales(shop, person) == 100
    update_customers_groups(Payment, payment)
    assert person.groups.count() == (initial_group_count + 1)
    assert bool([group for group in person.groups.all() if group.identifier == "diamond"])
    assert not bool([group for group in person.groups.all() if group.identifier in ["silver", "gold"]])


@pytest.mark.django_db
def test_sales_ranges_around_zero():
    shop = get_default_shop()
    person = create_random_person()
    initial_group_count = person.groups.count()
    sales_ranges = [
        ("silver", 0, 0),
        ("gold", 0, None),
        ("diamond", None, 0)
    ]
    for identifier, min, max in sales_ranges:
        create_sales_level(identifier, shop, min, max)

    assert _get_total_sales(shop, person) == 0
    _assign_to_group_based_on_sales(shop, person)
    assert person.groups.count() == (initial_group_count + 1)
    assert bool([group for group in person.groups.all() if group.identifier == "gold"])
