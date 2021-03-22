# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.core.models import AnonymousContact, CompanyContact, CustomerTaxGroup, PersonContact, get_person_contact
from shuup.testing.factories import (
    DEFAULT_IDENTIFIER,
    DEFAULT_NAME,
    create_random_company,
    create_random_person,
    get_default_customer_group,
)


@pytest.mark.django_db
def test_customers(django_user_model):
    users = [
        django_user_model.objects.create_user("Joe-%d" % x, "joe%d@example.com" % x, "password") for x in range(10)
    ]
    group = get_default_customer_group()
    assert str(group) == DEFAULT_NAME
    for user in users:
        contact = get_person_contact(user)
        group.members.add(contact)

    for user in users:
        assert PersonContact.objects.get(user=user).user_id == user.pk, "Customer profile found"
        assert DEFAULT_IDENTIFIER in user.contact.groups.values_list("identifier", flat=True), "Joe is now in the group"


@pytest.mark.django_db
def test_companies(django_user_model):
    peons = [
        django_user_model.objects.create_user("Peon-%d" % x, "Peon%d@example.com" % x, "password") for x in range(10)
    ]
    for cx in range(10):
        company = CompanyContact.objects.create(name="Company %d" % cx, tax_number="FI2101%d" % cx)
        assert str(company)
        for x in range(5):
            off = (cx * 3 + x) % len(peons)
            contact = get_person_contact(user=peons[off])
            company.members.add(contact)


@pytest.mark.django_db
def test_customer_tax_group1():
    # test that created person is assigned to proper group
    person = PersonContact.objects.create(email="test@example.com", name="Test Tester")
    assert person.tax_group.identifier == "default_person_customers"


@pytest.mark.django_db
def test_customer_tax_group2():
    # test that created company is assigned to proper group
    company = CompanyContact.objects.create(email="test@example.com", name="Test Tester", tax_number="FI123123")
    assert company.tax_group.identifier == "default_company_customers"


@pytest.mark.django_db
def test_customer_tax_group3(rf, admin_user):
    # SHUUP-1882
    assert type(CustomerTaxGroup.get_default_company_group().__str__()) == str


@pytest.mark.django_db
@pytest.mark.parametrize(
    "contact_cls,create_contact",
    [
        (AnonymousContact, AnonymousContact),
        (PersonContact, create_random_person),
        (CompanyContact, create_random_company),
    ],
)
def test_default_groups(contact_cls, create_contact):
    new_contact = create_contact()
    assert new_contact.groups.count() == 1
    default_group = new_contact.groups.first()
    assert type(CustomerTaxGroup.get_default_company_group().__str__()) == str
    assert default_group == new_contact.get_default_group()
    assert default_group.identifier == contact_cls.default_contact_group_identifier

    some_other_contact = create_contact()
    assert some_other_contact.groups.count() == 1

    if contact_cls != AnonymousContact:
        some_other_contact.groups.clear()
        some_other_contact.save()
        assert some_other_contact.groups.count() == 0  # Default group is only added while saving new contact
