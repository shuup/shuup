# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json
import pytest
from bs4 import BeautifulSoup
from django.contrib.auth import get_user, get_user_model
from django.contrib.auth.models import Group as PermissionGroup
from django.core import mail
from django.core.exceptions import PermissionDenied
from django.forms.models import modelform_factory
from django.http.response import Http404
from django.test import override_settings
from django.utils.encoding import force_text
from mock import patch
from rest_framework.serializers import raise_errors_on_nested_writes

from shuup.admin.modules.users.views import (
    LoginAsStaffUserView,
    LoginAsUserView,
    UserChangePermissionsView,
    UserDetailView,
    UserListView,
)
from shuup.admin.modules.users.views.permissions import PermissionChangeFormBase
from shuup.admin.template_helpers.shuup_admin import get_logout_url
from shuup.admin.utils.permissions import set_permissions_for_group
from shuup.admin.views.impersonate import stop_impersonating_staff
from shuup.core.models import Contact, get_person_contact
from shuup.testing.factories import (
    UserFactory,
    create_random_person,
    create_random_user,
    get_default_permission_group,
    get_default_shop,
)
from shuup.testing.soup_utils import extract_form_fields
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import reverse
from shuup.utils.excs import Problem
from shuup_tests.utils import printable_gibberish
from shuup_tests.utils.fixtures import regular_user


@pytest.mark.django_db
def test_user_detail_works_at_all(rf, admin_user):
    shop = get_default_shop()
    user = get_user_model().objects.create(
        username=printable_gibberish(20),
        first_name=printable_gibberish(10),
        last_name=printable_gibberish(10),
        password="suihku",
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

    user = get_user_model().objects.create(
        username=printable_gibberish(20),
        first_name=printable_gibberish(10),
        last_name=printable_gibberish(10),
        password="suihku",
        is_staff=True,
        is_superuser=False,
    )
    shop.staff_members.add(user)
    # non superusers can't see superusers
    with pytest.raises(Http404):
        view_func(apply_request_middleware(rf.get("/"), user=user), pk=admin_user.pk)


@pytest.mark.django_db
def test_user_detail_and_login_as_url(rf, admin_user):
    shop = get_default_shop()
    user = get_user_model().objects.create(
        username=printable_gibberish(20),
        first_name=printable_gibberish(10),
        last_name=printable_gibberish(10),
        password="suihkuunheti",
    )
    view_func = UserDetailView.as_view()
    response = view_func(apply_request_middleware(rf.get("/"), user=admin_user), pk=user.pk)
    assert response.status_code == 200
    response.render()
    assert force_text(user) in force_text(response.content)
    login_as_url = reverse("shuup_admin:user.login-as", kwargs={"pk": user.pk})
    assert force_text(login_as_url) in force_text(response.content)

    with override_settings(SHUUP_ADMIN_LOGIN_AS_REDIRECT_VIEW="giberish"):
        response = view_func(apply_request_middleware(rf.get("/"), user=admin_user), pk=user.pk)
        assert response.status_code == 200
        response.render()
        assert force_text(user) in force_text(response.content)
        login_as_url = reverse("shuup_admin:user.login-as", kwargs={"pk": user.pk})
        assert force_text(login_as_url) not in force_text(response.content)


@pytest.mark.django_db
def test_user_detail_as_staff_and_login_as_url(rf, admin_user):
    shop = get_default_shop()
    user = get_user_model().objects.create(
        username=printable_gibberish(20),
        first_name=printable_gibberish(10),
        last_name=printable_gibberish(10),
        password="suihkuunheti",
        is_staff=True,
    )
    view_func = UserDetailView.as_view()
    response = view_func(apply_request_middleware(rf.get("/"), user=admin_user), pk=user.pk)
    assert response.status_code == 200
    response.render()
    assert force_text(user) in force_text(response.content)
    login_as_staff_url = reverse("shuup_admin:user.login-as-staff", kwargs={"pk": user.pk})
    assert force_text(login_as_staff_url) in force_text(response.content)

    with override_settings(SHUUP_ADMIN_LOGIN_AS_STAFF_REDIRECT_VIEW="giberish"):
        response = view_func(apply_request_middleware(rf.get("/"), user=admin_user), pk=user.pk)
        assert response.status_code == 200
        response.render()
        assert force_text(user) in force_text(response.content)
        login_as_staff_url = reverse("shuup_admin:user.login-as-staff", kwargs={"pk": user.pk})
        assert force_text(login_as_staff_url) not in force_text(response.content)


@pytest.mark.django_db
def test_user_list(rf, admin_user):
    shop = get_default_shop()
    user = get_user_model().objects.create(
        username=printable_gibberish(20),
        first_name=printable_gibberish(10),
        last_name=printable_gibberish(10),
        password="suihku",
        is_staff=True,
        is_superuser=False,
    )
    shop.staff_members.add(user)
    view_func = UserListView.as_view()
    request = rf.get("/", {"jq": json.dumps({"perPage": 100, "page": 1})})

    # check with superuser
    response = view_func(apply_request_middleware(request, user=admin_user))
    assert response.status_code == 200
    data = json.loads(response.content.decode("utf-8"))
    assert len(data["items"]) == 2

    # check with staff user
    response = view_func(apply_request_middleware(request, user=user))
    assert response.status_code == 200
    data = json.loads(response.content.decode("utf-8"))
    assert len(data["items"]) == 1


@pytest.mark.django_db
def test_user_create(rf, admin_user):
    shop = get_default_shop()
    view_func = UserDetailView.as_view()
    before_count = get_user_model().objects.count()
    response = view_func(
        apply_request_middleware(
            rf.post(
                "/",
                {
                    "username": "test",
                    "email": "test@test.com",
                    "first_name": "test",
                    "last_name": "test",
                    "password": "test",
                    "send_confirmation": True,
                },
            ),
            user=admin_user,
        )
    )
    assert response.status_code == 302
    assert get_user_model().objects.count() == before_count + 1
    last_user = get_user_model().objects.last()
    assert last_user not in shop.staff_members.all()
    assert not len(mail.outbox), "mail not sent since user is not staff"

    response = view_func(
        apply_request_middleware(
            rf.post(
                "/",
                {
                    "username": "test3",
                    "email": "test3@test.com",
                    "first_name": "test",
                    "last_name": "test",
                    "password": "test",
                    "is_staff": True,
                    "send_confirmation": True,
                },
            ),
            user=admin_user,
        )
    )
    assert response.status_code == 302
    assert get_user_model().objects.count() == before_count + 2
    last_user = get_user_model().objects.last()
    assert last_user not in shop.staff_members.all()
    assert len(mail.outbox) == 1, "mail sent"

    user = get_user_model().objects.create(
        username=printable_gibberish(20),
        first_name=printable_gibberish(10),
        last_name=printable_gibberish(10),
        password="suihku",
        is_staff=True,
        is_superuser=False,
    )
    response = view_func(apply_request_middleware(rf.get("/"), user=user, skip_session=True))
    assert response.status_code == 200
    response.render()
    assert "Staff status" not in force_text(response.content)
    assert "Superuser status" not in force_text(response.content)

    # remove user staff permission
    view_func = UserChangePermissionsView.as_view()
    response = view_func(apply_request_middleware(rf.post("/", {"is_staff": False}), user=admin_user), pk=last_user.id)
    assert response.status_code == 302
    last_user = get_user_model().objects.last()
    assert last_user not in shop.staff_members.all()

    # add again, the member should not be inside shop staff member list
    view_func = UserChangePermissionsView.as_view()
    response = view_func(apply_request_middleware(rf.post("/", {"is_staff": True}), user=admin_user), pk=last_user.id)
    assert response.status_code == 302
    last_user = get_user_model().objects.last()
    assert last_user not in shop.staff_members.all()

    # create a superuser
    view_func = UserDetailView.as_view()
    response = view_func(
        apply_request_middleware(
            rf.post(
                "/",
                {
                    "username": "test4",
                    "email": "test4@test.com",
                    "first_name": "test",
                    "last_name": "test",
                    "password": "test",
                    "is_staff": True,
                    "is_superuser": True,
                    "send_confirmation": False,
                },
            ),
            user=admin_user,
        )
    )
    assert response.status_code == 302
    assert get_user_model().objects.count() == before_count + 4
    last_user = get_user_model().objects.last()
    # superuser shouldn't be added to staff members
    assert last_user not in shop.staff_members.all()

    # change the superuser
    response = view_func(
        apply_request_middleware(
            rf.post(
                "/",
                {
                    "username": "test487",
                    "email": "test4@test.com",
                    "first_name": "test2",
                    "last_name": "test",
                    "password": "test",
                    "is_staff": True,
                    "is_superuser": True,
                },
            ),
            user=admin_user,
        ),
        pk=last_user.pk,
    )
    assert response.status_code == 302
    assert get_user_model().objects.count() == before_count + 4
    last_user = get_user_model().objects.last()
    # superuser shouldn't be added to staff members
    assert last_user not in shop.staff_members.all()


@pytest.mark.django_db
def test_user_permission_view_as_staff_user(rf, admin_user):
    shop = get_default_shop()
    staff = create_random_user(is_staff=True)
    shop.staff_members.set([staff])

    user = create_random_user()

    # Staff shouldn't be able to see superuser status
    view_func = UserChangePermissionsView.as_view()
    response = view_func(apply_request_middleware(rf.get("/"), user=staff), pk=user.id)
    assert response.status_code == 200
    response.render()
    assert "Superuser (Full rights) status" not in force_text(response.content)

    # Superuser can see the superuser status
    assert admin_user.is_superuser
    view_func = UserChangePermissionsView.as_view()
    response = view_func(apply_request_middleware(rf.get("/"), user=admin_user), pk=user.id)
    assert response.status_code == 200
    response.render()
    assert "Superuser (Full rights) status" in force_text(response.content)


@pytest.mark.django_db
def test_user_detail_contact_seed(rf, admin_user):
    get_default_shop()
    contact = create_random_person()

    # Using random data for name and email would need escaping when
    # checking if it is rendered, therefore use something very basic instead
    contact.name = "Matti Perustyyppi"
    contact.email = "matti.perustyyppi@perus.fi"
    contact.save()

    view_func = UserDetailView.as_view()
    # Check that fields populate . . .
    request = apply_request_middleware(rf.get("/", {"contact_id": contact.pk}), user=admin_user)
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
    request = apply_request_middleware(rf.get("/", {"contact_id": contact.pk}), user=admin_user)
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
        model=get_user_model(), form=PermissionChangeFormBase, fields=("is_staff", "is_superuser")
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
    request = apply_request_middleware(rf.post("/"), user=regular_user, skip_session=True)

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
def test_login_as_staff_member(rf):
    shop = get_default_shop()
    staff_user = UserFactory(is_staff=True)
    permission_group = get_default_permission_group()
    staff_user.groups.add(permission_group)
    shop.staff_members.add(staff_user)

    view_func = LoginAsUserView.as_view()
    request = apply_request_middleware(rf.post("/"), user=staff_user, skip_session=True)

    # log in as self
    with pytest.raises(Problem):
        view_func(request, pk=staff_user.pk)

    user = UserFactory()
    get_person_contact(user)

    request = apply_request_middleware(rf.post("/"), user=staff_user)
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

    user.is_active = True
    user.save()

    # staff user without "user.login-as" permission trying to login as valid user
    with pytest.raises(PermissionDenied):
        view_func(request, pk=user.pk)

    permission_group = staff_user.groups.first()
    set_permissions_for_group(permission_group, ["user.login-as"])
    response = view_func(request, pk=user.pk)
    assert response["location"] == reverse("shuup:index")
    assert get_user(request) == user


@pytest.mark.django_db
def test_login_as_without_front_url(rf, admin_user, regular_user):
    get_default_shop()
    view_func = LoginAsUserView.as_view()
    request = apply_request_middleware(rf.post("/"), user=admin_user)

    def get_none():
        return None

    with patch("shuup.admin.modules.users.views.detail.get_front_url", side_effect=get_none):
        with pytest.raises(Problem):
            view_func(request, pk=regular_user.pk)


@pytest.mark.django_db
def test_login_as_requires_staff_member(rf, regular_user):
    shop = get_default_shop()
    staff_user = UserFactory(is_staff=True)
    permission_group = get_default_permission_group()
    staff_user.groups.add(permission_group)

    def do_nothing(request, shop=None):
        pass

    def get_default(request):
        return get_default_shop()

    # Maybe some vendors and non marketplace staff members has access to admin module
    with patch("shuup.admin.shop_provider.set_shop", side_effect=do_nothing):
        with patch("shuup.admin.shop_provider.get_shop", side_effect=get_default):
            view_func = LoginAsUserView.as_view()
            request = apply_request_middleware(rf.post("/"), user=staff_user)

            # not staff member
            with pytest.raises(PermissionDenied):
                view_func(request, pk=regular_user.pk)

            shop.staff_members.add(staff_user)

            # no permission
            with pytest.raises(PermissionDenied):
                view_func(request, pk=regular_user.pk)

            set_permissions_for_group(permission_group, ["user.login-as"])

            response = view_func(request, pk=regular_user.pk)
            assert response["location"] == reverse("shuup:index")
            assert get_user(request) == regular_user


@pytest.mark.django_db
def test_login_as_user(rf, admin_user, regular_user):
    get_default_shop()
    view_func = LoginAsUserView.as_view()
    request = apply_request_middleware(rf.post("/"), user=admin_user)
    get_person_contact(regular_user)
    response = view_func(request, pk=regular_user.pk)
    assert response["location"] == reverse("shuup:index")
    assert get_user(request) == regular_user


@pytest.mark.django_db
def test_login_as_staff_user(rf, admin_user):
    get_default_shop()
    staff_user = UserFactory(is_staff=True)
    view_func = LoginAsStaffUserView.as_view()

    request = apply_request_middleware(rf.post("/"), user=admin_user)
    context = dict(request=request)
    assert get_logout_url(context) == "/sa/logout/"
    response = view_func(request, pk=staff_user.pk)
    assert response["location"] == reverse("shuup_admin:dashboard")
    assert get_user(request) == staff_user
    assert get_logout_url(context) == "/sa/stop-impersonating-staff/"

    # Stop impersonating and since admin user have all access he should
    # be in user detail for staff user
    response = stop_impersonating_staff(request)
    assert response["location"] == reverse("shuup_admin:user.detail", kwargs={"pk": staff_user.pk})
    assert get_user(request) == admin_user


@pytest.mark.django_db
def test_login_as_staff_without_front_url(rf, admin_user, regular_user):
    get_default_shop()
    staff_user = UserFactory(is_staff=True)
    view_func = LoginAsStaffUserView.as_view()
    request = apply_request_middleware(rf.post("/"), user=admin_user)

    def get_none():
        return None

    with patch("shuup.admin.modules.users.views.detail.get_admin_url", side_effect=get_none):
        with pytest.raises(Problem):
            view_func(request, pk=staff_user.pk)


@pytest.mark.django_db
def test_login_as_staff_as_staff(rf):
    """
    Staff user 1 tries to impersonat staff user 2
    """
    shop = get_default_shop()
    staff_user1 = UserFactory(is_staff=True)
    permission_group = get_default_permission_group()
    staff_user1.groups.add(permission_group)
    shop.staff_members.add(staff_user1)

    staff_user2 = UserFactory(is_staff=True)

    view_func = LoginAsStaffUserView.as_view()
    request = apply_request_middleware(rf.post("/"), user=staff_user1)
    with pytest.raises(PermissionDenied):
        view_func(request, pk=staff_user2.pk)

    set_permissions_for_group(permission_group, ["user.login-as-staff"])

    response = view_func(request, pk=staff_user2.pk)
    assert response["location"] == reverse("shuup_admin:dashboard")
    assert get_user(request) == staff_user2

    # Stop impersonating and since staff1 does not have user detail permission
    # he/she should find him/herself from dashboard
    response = stop_impersonating_staff(request)
    assert response["location"] == reverse("shuup_admin:dashboard")
    assert get_user(request) == staff_user1

    response = stop_impersonating_staff(request)
    assert response.status_code == 403
