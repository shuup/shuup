# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from bs4 import BeautifulSoup
from django.contrib.auth import get_user, get_user_model
from django.contrib.auth.models import Group as PermissionGroup
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.forms.models import modelform_factory
from django.utils.encoding import force_text

from shuup.admin.modules.users.views import LoginAsUserView, UserDetailView
from shuup.admin.modules.users.views.permissions import \
    PermissionChangeFormBase
from shuup.core.models import Contact, get_person_contact
from shuup.testing.factories import (
    create_random_person, get_default_shop, UserFactory
)
from shuup.testing.soup_utils import extract_form_fields
from shuup.testing.utils import apply_request_middleware
from shuup.utils.excs import Problem
from shuup_tests.utils import printable_gibberish
from shuup_tests.utils.fixtures import regular_user


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


@pytest.mark.django_db
def test_user_permission_form_changes_group(rf, admin_user, regular_user):
    get_default_shop()
    form_class = modelform_factory(
        model=get_user_model(),
        form=PermissionChangeFormBase,
        fields=("is_staff", "is_superuser")
    )

    assert not regular_user.groups.all()

    group = PermissionGroup.objects.create(name="TestGroup")
    data = {"permission_groups": [group.pk]}
    form = form_class(changing_user=admin_user, instance=regular_user, data=data)
    form.save()

    assert group in regular_user.groups.all()

    form = form_class(changing_user=admin_user, instance=regular_user, data={})
    form.save()

    assert not regular_user.groups.all()


@pytest.mark.django_db
def test_login_as_user_errors(rf, admin_user, regular_user):
    get_default_shop()
    view_func = LoginAsUserView.as_view()
    request = apply_request_middleware(rf.post("/"), user=regular_user)

    # log in as self
    with pytest.raises(Problem):
        view_func(request, pk=regular_user.pk)

    user = UserFactory()
    get_person_contact(user)
    # non superuser trying to login as someone else
    with pytest.raises(PermissionDenied):
        view_func(request, pk=user.pk)

    request = apply_request_middleware(rf.post("/"), user=admin_user)
    user.is_superuser = True
    user.save()
    # user is trying to login as another superuser
    with pytest.raises(PermissionDenied):
        view_func(request, pk=user.pk)

    user.is_superuser = False
    user.is_staff = True
    user.save()
    # user is trying to login as a staff user
    with pytest.raises(PermissionDenied):
        view_func(request, pk=user.pk)

    user.is_staff = False
    user.is_active = False
    user.save()
    # user is trying to login as an inactive user
    with pytest.raises(Problem):
        view_func(request, pk=user.pk)


@pytest.mark.django_db
def test_login_as_user(rf, admin_user, regular_user):
    get_default_shop()
    view_func = LoginAsUserView.as_view()
    request = apply_request_middleware(rf.post("/"), user=admin_user)
    get_person_contact(regular_user)
    response = view_func(request, pk=regular_user.pk)
    assert response["location"] == reverse("shuup:index")
    assert get_user(request) == regular_user
