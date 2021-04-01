# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.utils.translation import activate

from shuup.admin.modules.contacts.views import ContactGroupMassEditView, ContactMassEditView
from shuup.core.models import Contact, ContactGroup, Gender
from shuup.testing.factories import create_random_person, get_default_shop
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_mass_edit_contacts(rf, admin_user):
    shop = get_default_shop()
    contact1 = create_random_person()
    contact2 = create_random_person()
    contact1.gender = Gender.FEMALE
    contact1.save()
    contact2.gender = Gender.FEMALE
    contact2.save()
    contact_ids = [contact1.pk, contact2.pk]
    request = apply_request_middleware(rf.post("/", data={"gender": Gender.MALE.value}), user=admin_user)
    request.session["mass_action_ids"] = contact_ids

    view = ContactMassEditView.as_view()
    response = view(request=request)
    assert response.status_code == 302
    for contact in Contact.objects.filter(id__in=contact_ids):
        assert contact.gender == Gender.MALE


@pytest.mark.django_db
def test_mass_edit_contacts2(rf, admin_user):
    activate("en")
    shop = get_default_shop()
    contact1 = create_random_person()
    contact2 = create_random_person()
    contact_group = ContactGroup.objects.create(name="test", shop=shop)
    data = {"contact_group": contact_group.pk}
    request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
    request.session["mass_action_ids"] = [contact1.pk, contact2.pk]

    view = ContactGroupMassEditView.as_view()
    response = view(request=request)
    assert response.status_code == 302
    contact_group = ContactGroup.objects.first()
    for contact in Contact.objects.all():
        assert contact in contact_group.members.all()
