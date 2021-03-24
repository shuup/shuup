# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import translation

from shuup.admin.modules.contacts.views.detail import ContactDetailView
from shuup.admin.modules.contacts.views.reset import ContactResetPasswordView
from shuup.core.models import ContactGroup
from shuup.testing.factories import create_random_person, get_default_shop
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_contact_details_view_with_many_groups(rf, admin_user):
    shop = get_default_shop()
    person = create_random_person()
    person.groups.add(
        ContactGroup.objects.create(name="Czz Group", shop=shop),
        ContactGroup.objects.create(name="Azz Group", shop=shop),
        ContactGroup.objects.create(name="Bzz Group", shop=shop),
        ContactGroup.objects.language("fi").create(name="Dzz ryhmä", shop=shop),
    )

    # Group with name in two languages
    grp_e = ContactGroup.objects.language("en").create(name="Ezz Group", shop=shop)
    grp_e.set_current_language("fi")
    grp_e.name = "Ezz ryhmä"
    grp_e.save()
    person.groups.add(grp_e)

    request = apply_request_middleware(rf.get("/"), user=admin_user)
    with translation.override("en"):
        view_func = ContactDetailView.as_view()
        response = view_func(request, pk=person.pk)
    content = response.render().content.decode("utf-8")
    assert "Azz Group" in content
    assert "Bzz Group" in content
    assert "Czz Group" in content
    assert "Dzz ryhmä" in content, "no name in active language, still present"
    assert "Ezz Group" in content, "rendered with active language"
    positions = [content.index(x + "zz ") for x in "ABCDE"]
    assert positions == sorted(positions), "Groups are sorted"
    assert response.status_code == 200


@pytest.mark.django_db
def test_admin_recovers_clients_password(rf, admin_user):
    get_default_shop()
    person = create_random_person()
    person.user = get_user_model().objects.create_user(
        username="random_person", password="asdfg", email="random@shuup.local"
    )
    person.save()
    request = apply_request_middleware(rf.post("/"), user=admin_user)
    view_func = ContactResetPasswordView.as_view()
    n_outbox_pre = len(mail.outbox)
    view_func(request, pk=person.pk)  # The response doesn't actually matter.
    assert len(mail.outbox) == n_outbox_pre + 1, "Sending recovery email has failed"
