# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.forms import formset_factory

from shoop.admin.modules.contact_groups.views.edit import ContactGroupEditView
from shoop.admin.modules.contact_groups.views.forms import ContactGroupMembersForm, ContactGroupMembersFormSet
from shoop.testing.factories import create_random_person, get_default_customer_group
from shoop_tests.utils.forms import get_form_data


@pytest.mark.django_db
def test_contact_group_members_formset(rf):
    FormSet = formset_factory(ContactGroupMembersForm, ContactGroupMembersFormSet, extra=1, can_delete=True)
    contact_group = get_default_customer_group()
    person = create_random_person()

    # No members
    formset = FormSet(contact_group=contact_group)
    assert formset.initial_form_count() == 0

    # Add a member
    data = dict(get_form_data(formset, True), **{"form-0-member": person.pk})
    formset = FormSet(contact_group=contact_group, data=data)
    formset.save()
    assert contact_group.members.filter(pk=person.pk).exists()

    # Remove a member
    formset = FormSet(contact_group=contact_group)
    assert formset.initial_form_count() == 1
    data = dict(get_form_data(formset, True), **{"form-0-DELETE": "1"})
    formset = FormSet(contact_group=contact_group, data=data)
    formset.save()
    assert not contact_group.members.exists()
