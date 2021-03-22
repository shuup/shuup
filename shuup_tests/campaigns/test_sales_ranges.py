# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import pytest
from django.core.exceptions import ValidationError

from shuup.campaigns.models import ContactGroupSalesRange
from shuup.campaigns.signal_handlers import update_customers_groups
from shuup.campaigns.utils.sales_range import assign_to_group_based_on_sales, get_total_sales
from shuup.core.models import AnonymousContact, ContactGroup, Payment, PersonContact
from shuup.testing.factories import (
    create_order_with_product,
    create_product,
    create_random_company,
    create_random_person,
    get_default_customer_group,
    get_default_shop,
    get_default_supplier,
)


@pytest.mark.django_db
@pytest.mark.parametrize("get_contact", [AnonymousContact, create_random_company, create_random_person])
def test_sales_ranges_for_default_groups(get_contact):
    shop = get_default_shop()
    group = get_contact().get_default_group()

    with pytest.raises(ValidationError):
        ContactGroupSalesRange.objects.create(group=group, shop=shop, min_value=1, max_value=100)


def create_fully_paid_order(shop, customer, supplier, product_sku, price_value):
    product = create_product(product_sku, shop=shop, supplier=supplier, default_price=price_value)
    order = create_order_with_product(
        product=product, supplier=supplier, quantity=1, taxless_base_unit_price=price_value, shop=get_default_shop()
    )
    order.customer = customer
    order.save()
    order.cache_prices()
    return order.create_payment(order.taxful_total_price)


def create_sales_range(group, shop, minimum, maximum):
    contact_group, _ = ContactGroup.objects.get_or_create(identifier=group, shop=shop)
    return ContactGroupSalesRange.objects.create(group=contact_group, shop=shop, min_value=minimum, max_value=maximum)


@pytest.mark.django_db
def test_sales_ranges_basic():
    shop = get_default_shop()
    supplier = get_default_supplier()
    default_group = get_default_customer_group()
    # Create non active range for default group
    ContactGroupSalesRange.objects.create(group=default_group, shop=shop, min_value=0, max_value=0)
    person = create_random_person()
    default_group.members.add(person)
    initial_group_count = person.groups.count()
    sales_ranges = [("silver", 0, 50), ("gold", 50, 100), ("diamond", 100, 1000)]
    for identifier, min, max in sales_ranges:
        create_sales_range(identifier, shop, min, max)

    payment = create_fully_paid_order(shop, person, supplier, "sku1", 10)
    assert get_total_sales(shop, person) == 10
    update_customers_groups(Payment, payment)
    assert person.groups.count() == (initial_group_count + 1)
    assert bool([group for group in person.groups.all() if group.identifier == "silver"])
    # Since group has inactive range person shouldn't be removed from it
    assert bool([group for group in person.groups.all() if group == default_group])

    payment = create_fully_paid_order(shop, person, supplier, "sku2", 50)
    assert get_total_sales(shop, person) == 60
    update_customers_groups(Payment, payment)
    assert person.groups.count() == (initial_group_count + 1)
    assert bool([group for group in person.groups.all() if group.identifier == "gold"])
    # Since group has inactive range person shouldn't be removed from it
    assert bool([group for group in person.groups.all() if group == default_group])

    payment = create_fully_paid_order(shop, person, supplier, "sku3", 200)
    assert get_total_sales(shop, person) == 260
    update_customers_groups(Payment, payment)
    assert person.groups.count() == (initial_group_count + 1)
    assert bool([group for group in person.groups.all() if group.identifier == "diamond"])
    # Since group has inactive range person shouldn't be removed from it
    assert bool([group for group in person.groups.all() if group == default_group])


@pytest.mark.django_db
def test_max_amount_none():
    shop = get_default_shop()
    supplier = get_default_supplier()
    person = create_random_person()
    initial_group_count = person.groups.count()
    sales_ranges = [("silver", 0, 50), ("gold", 50, None), ("diamond", 100, None)]
    for identifier, min, max in sales_ranges:
        create_sales_range(identifier, shop, min, max)

    payment = create_fully_paid_order(shop, person, supplier, "sku3", 200)
    assert get_total_sales(shop, person) == 200
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
    sales_ranges = [("wood", 15, 0), ("silver", 0, 50), ("diamond", 100, None)]
    for identifier, min, max in sales_ranges:
        create_sales_range(identifier, shop, min, max)

    payment = create_fully_paid_order(shop, person, supplier, "sku1", 10)
    assert get_total_sales(shop, person) == 10
    update_customers_groups(Payment, payment)
    assert person.groups.count() == (initial_group_count + 1)
    assert bool([group for group in person.groups.all() if group.identifier == "silver"])
    assert not bool([group for group in person.groups.all() if group.identifier == "wood"])

    payment = create_fully_paid_order(shop, person, supplier, "sku2", 50)
    assert get_total_sales(shop, person) == 60
    update_customers_groups(Payment, payment)
    assert person.groups.count() == initial_group_count
    assert not bool([group for group in person.groups.all() if group.identifier in ["silver", "gold", "diamond"]])

    payment = create_fully_paid_order(shop, person, supplier, "sku3", 200)
    assert get_total_sales(shop, person) == 260
    update_customers_groups(Payment, payment)
    assert person.groups.count() == (initial_group_count + 1)
    assert bool([group for group in person.groups.all() if group.identifier == "diamond"])


@pytest.mark.django_db
def test_min_amount_is_not_included():
    shop = get_default_shop()
    supplier = get_default_supplier()
    person = create_random_person()
    initial_group_count = person.groups.count()
    sales_ranges = [("silver", 0, 50), ("gold", 50, 100), ("diamond", 100, 1000), ("reverse_diamond", 1000, 100)]
    for identifier, min, max in sales_ranges:
        create_sales_range(identifier, shop, min, max)

    payment = create_fully_paid_order(shop, person, supplier, "sku1", 50)
    assert get_total_sales(shop, person) == 50
    update_customers_groups(Payment, payment)
    assert person.groups.count() == (initial_group_count + 1)
    assert bool([group for group in person.groups.all() if group.identifier == "gold"])
    assert not bool([group for group in person.groups.all() if group.identifier in ["silver", "diamond"]])

    payment = create_fully_paid_order(shop, person, supplier, "sku2", 50)
    assert get_total_sales(shop, person) == 100
    update_customers_groups(Payment, payment)
    assert person.groups.count() == (initial_group_count + 1)
    assert bool([group for group in person.groups.all() if group.identifier == "diamond"])
    assert not bool([group for group in person.groups.all() if group.identifier == "reverse_diamond"])
    assert not bool([group for group in person.groups.all() if group.identifier in ["silver", "gold"]])


@pytest.mark.django_db
def test_sales_ranges_around_zero():
    shop = get_default_shop()
    person = create_random_person()
    initial_group_count = person.groups.count()
    sales_ranges = [("silver", 0, 0), ("gold", 0, None), ("diamond", None, 0)]
    for identifier, min, max in sales_ranges:
        create_sales_range(identifier, shop, min, max)

    assert get_total_sales(shop, person) == 0
    assign_to_group_based_on_sales(ContactGroupSalesRange, shop, person)
    assert person.groups.count() == (initial_group_count + 1)
    assert bool([group for group in person.groups.all() if group.identifier == "gold"])


@pytest.mark.django_db
def test_active_ranges():
    shop = get_default_shop()
    sales_ranges = [
        ("wood", None, None),
        ("silver", 0, 0),
        ("gold", None, 23),
        ("diamond", None, 0),
        ("active", 0, None),
        (PersonContact.default_contact_group_identifier, 0, 1),  # should cause error when creating range.
    ]
    for identifier, min, max in sales_ranges:
        if identifier == PersonContact.default_contact_group_identifier:
            with pytest.raises(ValidationError):
                create_sales_range(identifier, shop, min, max)
        else:
            create_sales_range(identifier, shop, min, max)

    assert ContactGroupSalesRange.objects.active(shop).count() == 1
    assert ContactGroupSalesRange.objects.active(shop).first().group.identifier == "active"


@pytest.mark.django_db
def test_sales_ranges_update_after_range_update():
    shop = get_default_shop()
    supplier = get_default_supplier()
    person = create_random_person()
    company = create_random_company()
    create_fully_paid_order(shop, person, supplier, "sku1", 50)
    create_fully_paid_order(shop, company, supplier, "sku2", 100)
    assert get_total_sales(shop, person) == 50
    assert get_total_sales(shop, company) == 100

    sales_range = create_sales_range("gold", shop, 10, 90)
    assert sales_range.group in person.groups.all()
    assert sales_range.group not in company.groups.all()

    sales_range.max_value = None
    sales_range.save()
    assert sales_range.group in person.groups.all()
    assert sales_range.group in company.groups.all()

    # Make sure customers is actually removed when range changes
    sales_range.max_value = 60
    sales_range.save()
    assert sales_range.group in person.groups.all()
    assert sales_range.group not in company.groups.all()

    # Inactive ranges shouldn't update group members
    sales_range.min_value = None
    sales_range.save()
    assert sales_range.group in person.groups.all()
    assert sales_range.group not in company.groups.all()
