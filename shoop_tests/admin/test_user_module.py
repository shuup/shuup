# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from bs4 import BeautifulSoup
from django.contrib.auth import get_user_model
from django.utils.encoding import force_text

from shoop.admin.modules.users.views import UserDetailView
from shoop.core.models.contacts import Contact
from shoop.testing.factories import create_random_person, get_default_shop
from shoop.testing.soup_utils import extract_form_fields
from shoop.testing.utils import apply_request_middleware
from shoop.utils.excs import Problem
from shoop_tests.utils import printable_gibberish


@pytest.mark.django_db
def test_user_detail_works_at_all(rf, admin_user):
    get_default_shop()
    user = get_user_model().objects.create(
        username=printable_gibberish(20),
        first_name=printable_gibberish(10),
        last_name=printable_gibberish(10),
        password="suihku"
    )
    view_func = UserDetailView.as_view()
    response = view_func(apply_request_middleware(rf.get("/"), user=admin_user), pk=user.pk)
    assert response.status_code == 200
    response.render()
    assert force_text(user) in force_text(response.content)
    response = view_func(apply_request_middleware(rf.post("/", {"set_is_active": "0"}), user=admin_user), pk=user.pk)
    assert response.status_code < 500 and not get_user_model().objects.get(pk=user.pk).is_active
    with pytest.raises(Problem):
        view_func(apply_request_middleware(rf.post("/", {"set_is_active": "0"}), user=admin_user), pk=admin_user.pk)


@pytest.mark.django_db
def test_user_detail_contact_seed(rf):
    get_default_shop()
    contact = create_random_person()

    # Using random data for name and email would need escaping when
    # checking if it is rendered, therefore use something very basic instead
    contact.name = "Matti Perustyyppi"
    contact.email = "matti.perustyyppi@perus.fi"
    contact.save()

    view_func = UserDetailView.as_view()
    # Check that fields populate . . .
    request = apply_request_middleware(rf.get("/", {"contact_id": contact.pk}))
    response = view_func(request)
    response.render()
    content = force_text(response.content)
    assert force_text(contact.first_name) in content
    assert force_text(contact.last_name) in content
    assert force_text(contact.email) in content
    # POST the password too to create the user . . .
    post = extract_form_fields(BeautifulSoup(content))
    post["password"] = "HELLO WORLD"
    request.method = "POST"
    request.POST = post
    response = view_func(request)
    assert response.status_code < 500
    # Check this new user is visible in the details now
    user = Contact.objects.get(pk=contact.pk).user
    request = apply_request_middleware(rf.get("/", {"contact_id": contact.pk}))
    response = view_func(request, pk=user.pk)
    response.render()
    content = force_text(response.content)
    assert force_text(contact.first_name) in content
    assert force_text(contact.last_name) in content
    assert force_text(contact.email) in content
