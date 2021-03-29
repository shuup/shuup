# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME, get_user, get_user_model, logout
from django.core.exceptions import ValidationError
from django.forms import ValidationError

from shuup.apps.provides import override_provides
from shuup.front.apps.auth.forms import EmailAuthenticationForm
from shuup.front.signals import login_allowed
from shuup.testing.factories import get_default_shop
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import is_anonymous, reverse
from shuup_tests.front.utils import FieldTestProvider, login_allowed_signal
from shuup_tests.utils.fixtures import REGULAR_USER_PASSWORD, regular_user

regular_user = regular_user  # noqa

pytestmark = pytest.mark.skipif(
    "shuup.front.apps.auth" not in settings.INSTALLED_APPS, reason="Need shuup.front.apps.auth in INSTALLED_APPS"
)


def prepare_user(user):
    user.is_active = True
    user.set_password(REGULAR_USER_PASSWORD)
    user.save(update_fields=("is_active", "password"))


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_login_with_invalid_password(client, regular_user, rf):
    get_default_shop()
    prepare_user(regular_user)
    redirect_target = "/redirect-success/"
    response = client.post(
        reverse("shuup:login"),
        data={
            "username": regular_user.email,
            "password": "hello",
            REDIRECT_FIELD_NAME: redirect_target,
        },
    )

    assert not response.get("location")  # No redirect since errors

    request = rf.get("/")
    request.session = client.session
    assert is_anonymous(get_user(request)), "User is still anonymous"


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_login_logs_the_user_in(client, regular_user, rf):
    get_default_shop()
    prepare_user(regular_user)
    redirect_target = "/redirect-success/"
    response = client.post(
        reverse("shuup:login"),
        data={
            "username": regular_user.username,
            "password": REGULAR_USER_PASSWORD,
            REDIRECT_FIELD_NAME: redirect_target,
        },
    )

    assert response.get("location")
    assert response.get("location").endswith(redirect_target)

    request = rf.get("/")
    request.session = client.session
    assert get_user(request) == regular_user, "User is logged in"


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_login_fails_without_valid_password(client, regular_user, rf):
    prepare_user(regular_user)
    get_default_shop()
    client.post(
        reverse("shuup:login"),
        data={
            "username": regular_user.username,
            "password": "x%s" % REGULAR_USER_PASSWORD,
        },
    )
    request = rf.get("/")
    request.session = client.session
    assert is_anonymous(get_user(request)), "User is still anonymous"


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_login_with_email_1(client, regular_user, rf):
    get_default_shop()
    prepare_user(regular_user)
    redirect_target = "/redirect-success/"
    response = client.post(
        reverse("shuup:login"),
        data={"username": regular_user.email, "password": REGULAR_USER_PASSWORD, REDIRECT_FIELD_NAME: redirect_target},
    )

    assert response.get("location")
    assert response.get("location").endswith(redirect_target)

    request = rf.get("/")
    request.session = client.session
    assert get_user(request) == regular_user, "User is logged in"


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_login_with_email_2(client, regular_user, rf):
    # Create user with same email as regular user to fail login
    get_user_model().objects.create_user(username="el_person", password="123123", email=regular_user.email)

    get_default_shop()
    prepare_user(regular_user)
    redirect_target = "/redirect-success/"
    client.post(
        reverse("shuup:login"),
        data={"username": regular_user.email, "password": REGULAR_USER_PASSWORD, REDIRECT_FIELD_NAME: redirect_target},
    )

    request = rf.get("/")
    request.session = client.session
    assert is_anonymous(get_user(request)), "User is still anonymous"

    # Login with unknown email
    client.post(
        reverse("shuup:login"),
        data={
            "username": "unknown@example.com",
            "password": REGULAR_USER_PASSWORD,
            REDIRECT_FIELD_NAME: redirect_target,
        },
    )

    request = rf.get("/")
    request.session = client.session
    assert is_anonymous(get_user(request)), "User is still anonymous"

    # Login with username should work normally
    response = client.post(
        reverse("shuup:login"),
        data={
            "username": regular_user.username,
            "password": REGULAR_USER_PASSWORD,
            REDIRECT_FIELD_NAME: redirect_target,
        },
    )

    assert response.get("location")
    assert response.get("location").endswith(redirect_target)

    request = rf.get("/")
    request.session = client.session
    assert get_user(request) == regular_user, "User is logged in"


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_login_with_email_3(client, regular_user, rf):
    new_user_password = "123123"
    new_user = get_user_model().objects.create_user(
        username=regular_user.email, password=new_user_password, email=regular_user.email
    )

    get_default_shop()
    prepare_user(regular_user)
    redirect_target = "/redirect-success/"

    # Login with new_user username should work even if there is users with same email
    response = client.post(
        reverse("shuup:login"),
        data={"username": regular_user.email, "password": new_user_password, REDIRECT_FIELD_NAME: redirect_target},
    )

    assert response.get("location")
    assert response.get("location").endswith(redirect_target)

    request = rf.get("/")
    request.session = client.session
    assert get_user(request) == new_user, "User is logged in"


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_login_inactive_user_fails(client, regular_user, rf):
    get_default_shop()
    prepare_user(regular_user)

    client.post(
        reverse("shuup:login"),
        data={
            "username": regular_user.username,
            "password": REGULAR_USER_PASSWORD,
        },
    )

    request = rf.get("/")
    request.session = client.session
    assert get_user(request) == regular_user, "User is logged in"

    request = rf.get("/")
    request.session = client.session
    logout(request)

    user_contact = regular_user.contact
    assert user_contact.is_active

    user_contact.is_active = False
    user_contact.save()

    client.post(
        reverse("shuup:login"),
        data={
            "username": regular_user.username,
            "password": REGULAR_USER_PASSWORD,
        },
    )

    request = rf.get("/")
    request.session = client.session
    assert is_anonymous(get_user(request)), "User is still anonymous"


@pytest.mark.django_db
def test_recover_password_form_with_invalid_email():
    from shuup.core.utils.forms import RecoverPasswordForm

    form = RecoverPasswordForm({"username": "fake_username", "email": "invalid_email"})

    assert (len(form.errors) == 1) and form.errors["email"]


@pytest.mark.django_db
def test_email_auth_form_with_inactive_user(client, regular_user, rf):
    shop = get_default_shop()
    prepare_user(regular_user)

    client.post(
        reverse("shuup:login"),
        data={
            "username": regular_user.username,
            "password": REGULAR_USER_PASSWORD,
        },
    )

    request = rf.get("/")
    request.session = client.session
    assert get_user(request) == regular_user, "User is logged in"

    request = rf.get("/")
    request.session = client.session
    logout(request)

    user_contact = regular_user.contact
    assert user_contact.is_active

    user_contact.is_active = False
    user_contact.save()

    payload = {
        "username": regular_user.username,
        "password": REGULAR_USER_PASSWORD,
    }

    request = apply_request_middleware(rf.get("/"), shop=shop)

    form = EmailAuthenticationForm(request=request, data=payload)
    assert not form.is_valid()

    with pytest.raises(ValidationError) as e:
        form.confirm_login_allowed(regular_user)

    assert list(e.value)[0] == "This account is inactive."


@pytest.mark.django_db
def test_email_auth_form(rf, regular_user):
    shop = get_default_shop()
    prepare_user(regular_user)
    request = apply_request_middleware(rf.get("/"), shop=shop)
    with override_provides("front_auth_form_field_provider", ["shuup_tests.front.utils.FieldTestProvider"]):
        payload = {}
        form = EmailAuthenticationForm(request=request, data=payload)
        assert not form.is_valid()
        assert form.errors["username"][0] == "This field is required."
        assert form.errors["password"][0] == "This field is required."

        payload.update({"username": regular_user.username})
        form = EmailAuthenticationForm(request=request, data=payload)
        assert not form.is_valid()
        assert "username" not in list(form.errors)
        assert form.errors["password"][0] == "This field is required."

        payload.update({"password": REGULAR_USER_PASSWORD})
        form = EmailAuthenticationForm(request=request, data=payload)
        assert FieldTestProvider.key in form.fields
        assert not form.is_valid()
        assert form.errors[FieldTestProvider.key][0] == FieldTestProvider.error_msg

        # accept terms
        payload.update({FieldTestProvider.key: True})
        form = EmailAuthenticationForm(request=request, data=payload)
        assert FieldTestProvider.key in form.fields
        assert form.is_valid()

        login_allowed.connect(login_allowed_signal, dispatch_uid="test_login_allowed")
        with pytest.raises(ValidationError):
            form.confirm_login_allowed(regular_user)
        login_allowed.disconnect(dispatch_uid="test_login_allowed")
        form.confirm_login_allowed(regular_user)
