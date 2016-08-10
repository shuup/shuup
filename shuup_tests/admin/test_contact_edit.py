# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.contrib.auth import get_user_model

from shuup.admin.forms.fields import Select2MultipleField
from shuup.admin.modules.contacts.forms import (
    CompanyContactBaseForm, PersonContactBaseForm
)
from shuup.core.models import (
    CompanyContact, Gender, get_person_contact, PersonContact
)
from shuup.testing.factories import create_random_company, create_random_person
from shuup_tests.utils import printable_gibberish


@pytest.mark.django_db
def test_person_contact_create_form():
    user = get_user_model().objects.create_user(
        username=printable_gibberish(),
        first_name=printable_gibberish(),
        last_name=printable_gibberish(),
    )
    test_first_name = printable_gibberish()
    test_last_name = printable_gibberish()
    contact_base_form = PersonContactBaseForm(data={
        "first_name": test_first_name,
        "last_name": test_last_name,
        "gender": Gender.UNDISCLOSED.value
    }, user=user)
    assert contact_base_form.is_valid(), contact_base_form.errors
    contact = contact_base_form.save()
    assert isinstance(contact, PersonContact)
    assert contact.user == user
    assert get_person_contact(user) == contact
    assert contact.name == "%s %s" % (test_first_name, test_last_name)


@pytest.mark.django_db
def test_person_contact_edit_form():
    person = create_random_person()
    new_first_name = "test first name"
    new_name = "%s %s" % (new_first_name, person.last_name)
    contact_base_form = PersonContactBaseForm(instance=person, data={
        "first_name": "test first name",
        "last_name": person.last_name,
        "gender": person.gender.value
    })
    assert contact_base_form.is_valid(), contact_base_form.errors
    contact = contact_base_form.save()
    assert isinstance(contact, PersonContact)
    assert contact.first_name == new_first_name
    assert contact.name == new_name


@pytest.mark.django_db
def test_company_contact_create_form():
    company_name = "test company"
    contact_base_form = CompanyContactBaseForm(data={
        "name": company_name,
    })
    assert contact_base_form.is_valid(), contact_base_form.errors
    contact = contact_base_form.save()
    assert isinstance(contact, CompanyContact)
    assert contact.name == company_name


@pytest.mark.django_db
def test_company_contact_edit_form():
    company = create_random_company()
    new_company_name = "test company"
    contact_base_form = CompanyContactBaseForm(instance=company, data={
        "name": new_company_name,
    })
    assert contact_base_form.is_valid(), contact_base_form.errors
    contact = contact_base_form.save()
    assert isinstance(contact, CompanyContact)
    assert isinstance(contact_base_form.fields["members"], Select2MultipleField)
    assert contact.name == new_company_name
