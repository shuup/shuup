# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from django.contrib.auth import get_user_model

from shoop.admin.forms.fields import Select2MultipleField
from shoop.admin.modules.contacts.views.edit import ContactBaseForm
from shoop.core.models import (
    CompanyContact, Gender, get_person_contact, PersonContact
)
from shoop.testing.factories import create_random_company
from shoop_tests.utils import printable_gibberish


@pytest.mark.django_db
def test_contact_edit_form():
    user = get_user_model().objects.create_user(
        username=printable_gibberish(),
        first_name=printable_gibberish(),
        last_name=printable_gibberish(),
    )
    test_first_name = printable_gibberish()
    test_last_name = printable_gibberish()
    contact_base_form = ContactBaseForm(bind_user=user, data={
        "first_name": test_first_name,
        "last_name": test_last_name,
        "gender": Gender.UNDISCLOSED.value
    })
    assert contact_base_form.bind_user == user
    assert contact_base_form.contact_class == PersonContact
    assert contact_base_form.is_valid(), contact_base_form.errors
    contact = contact_base_form.save()
    assert isinstance(contact, PersonContact)
    assert contact.user == user
    assert get_person_contact(user) == contact
    assert contact.name == "%s %s" % (test_first_name, test_last_name)


@pytest.mark.django_db
def test_company_contact_edit_form():
    company = create_random_company()
    contact_base_form = ContactBaseForm(instance=company, data={
        "name": company.name,
    })
    assert not contact_base_form.bind_user
    assert contact_base_form.contact_class == CompanyContact
    assert contact_base_form.is_valid(), contact_base_form.errors
    contact = contact_base_form.save()
    assert isinstance(contact, CompanyContact)
    assert isinstance(contact_base_form.fields["members"], Select2MultipleField)


@pytest.mark.django_db
def test_creating_contact():
    persons_count = PersonContact.objects.count()
    contact_base_form = ContactBaseForm(data={
        "type": "PersonContact",
        "name": printable_gibberish(),
        "gender": Gender.UNDISCLOSED.value
    })
    assert contact_base_form.is_valid(), contact_base_form.errors
    contact = contact_base_form.save()
    assert isinstance(contact, PersonContact)
    assert contact.pk is not None
    assert PersonContact.objects.count() == (persons_count + 1)
