# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.contrib.auth import get_user_model

from shoop.admin.modules.contacts.views.edit import ContactBaseForm
from shoop.core.models import Gender, get_person_contact, PersonContact
from shoop_tests.utils import printable_gibberish


@pytest.mark.django_db
def test_contact_edit_form():
    user = get_user_model().objects.create_user(
        username=printable_gibberish(),
        first_name=printable_gibberish(),
        last_name=printable_gibberish(),
    )
    contact_base_form = ContactBaseForm(bind_user=user, data={
        "name": "herf durr",
        "gender": Gender.UNDISCLOSED.value
    })
    assert contact_base_form.bind_user == user
    assert contact_base_form.contact_class == PersonContact
    assert contact_base_form.is_valid(), contact_base_form.errors
    contact = contact_base_form.save()
    assert isinstance(contact, PersonContact)
    assert contact.user == user
    assert get_person_contact(user) == contact
