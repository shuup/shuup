# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shoop.admin.modules.taxes.views import CustomerTaxGroupListView
from shoop.core.models import (
    CompanyContact, CustomerTaxGroup, get_person_contact, PersonContact
)
from shoop.testing.factories import (
    create_random_company, DEFAULT_IDENTIFIER, DEFAULT_NAME,
    get_default_customer_group, get_default_shop
)
from shoop.testing.utils import apply_request_middleware
from shoop.utils.importing import load


@pytest.mark.django_db
def test_customers(django_user_model):
    users = [django_user_model.objects.create_user('Joe-%d' % x, 'joe%d@example.com' % x, 'password') for x in range(10)]
    group = get_default_customer_group()
    assert str(group) == DEFAULT_NAME
    for user in users:
        contact = get_person_contact(user)
        group.members.add(contact)

    for user in users:
        assert PersonContact.objects.get(user=user).user_id == user.pk, "Customer profile found"
        assert tuple(user.contact.groups.values_list("identifier", flat=True)) == (DEFAULT_IDENTIFIER,), "Joe is now in the group"


@pytest.mark.django_db
def test_companies(django_user_model):
    peons = [django_user_model.objects.create_user('Peon-%d' % x, 'Peon%d@example.com' % x, 'password') for x in range(10)]
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
    # SHOOP-1882
    assert type(CustomerTaxGroup.get_default_company_group().__str__()) == str
