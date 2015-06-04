# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from shoop.core.models import CompanyContact, PersonContact, get_person_contact
from shoop.testing.factories import DEFAULT_NAME, get_default_customer_group, DEFAULT_IDENTIFIER


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
        company = CompanyContact.objects.create(name="Company %d" % cx, vat_code="FI2101%d" % cx)
        assert str(company)
        for x in range(5):
            off = (cx * 3 + x) % len(peons)
            contact = get_person_contact(user=peons[off])
            company.members.add(contact)
