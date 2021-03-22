# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.forms import formset_factory
from django.utils.encoding import force_text

from shuup.admin.modules.contact_groups.views import ContactGroupEditView
from shuup.admin.modules.contact_groups.views.forms import ContactGroupMembersForm, ContactGroupMembersFormSet
from shuup.core.models import AnonymousContact
from shuup.testing.factories import (
    create_random_company,
    create_random_person,
    get_default_customer_group,
    get_default_shop,
)
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import reverse
from shuup_tests.utils.forms import get_form_data


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


def check_for_delete(request, contact_group, can_delete):
    delete_url = reverse("shuup_admin:contact_group.delete", kwargs={"pk": contact_group.pk})
    view = ContactGroupEditView.as_view()
    response = view(request, pk=contact_group.pk).render()
    assert bool(delete_url in force_text(response.content)) == can_delete


@pytest.mark.parametrize(
    "contact",
    [
        AnonymousContact,
        create_random_company,
        create_random_person,
    ],
)
@pytest.mark.django_db
def test_protected_contact_groups(rf, admin_user, contact):
    get_default_shop()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    check_for_delete(request, contact().get_default_group(), False)


@pytest.mark.django_db
def test_contact_group_delete_button(rf, admin_user):
    get_default_shop()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    check_for_delete(request, get_default_customer_group(), True)
