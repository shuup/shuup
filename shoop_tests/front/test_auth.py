# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.conf import settings
from django.contrib.auth import get_user, REDIRECT_FIELD_NAME, get_user_model
from django.core.urlresolvers import reverse
from shoop.testing.factories import get_default_shop
from shoop_tests.utils.fixtures import REGULAR_USER_PASSWORD, regular_user

regular_user = regular_user  # noqa


def prepare_user(user):
    user.is_active = True
    user.set_password(REGULAR_USER_PASSWORD)
    user.save(update_fields=("is_active", "password"))


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_login_logs_the_user_in(client, regular_user, rf):
    if "shoop.front.apps.auth" not in settings.INSTALLED_APPS:
        pytest.skip("Need shoop.front.apps.auth in INSTALLED_APPS")

    get_default_shop()
    prepare_user(regular_user)
    redirect_target = "/redirect-success/"
    response = client.post(reverse("shoop:login"), data={
        "username": regular_user.username,
        "password": REGULAR_USER_PASSWORD,
        REDIRECT_FIELD_NAME: redirect_target
    })

    assert response.get("location")
    assert response.get("location").endswith(redirect_target)

    request = rf.get("/")
    request.session = client.session
    assert get_user(request) == regular_user, "User is logged in"


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_login_fails_without_valid_password(client, regular_user, rf):
    if "shoop.front.apps.auth" not in settings.INSTALLED_APPS:
        pytest.skip("Need shoop.front.apps.auth in INSTALLED_APPS")
    prepare_user(regular_user)
    get_default_shop()
    client.post(reverse("shoop:login"), data={
        "username": regular_user.username,
        "password": "x%s" % REGULAR_USER_PASSWORD,
    })
    request = rf.get("/")
    request.session = client.session
    assert get_user(request).is_anonymous(), "User is still anonymous"


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_login_with_email_1(client, regular_user, rf):
    if "shoop.front.apps.auth" not in settings.INSTALLED_APPS:
        pytest.skip("Need shoop.front.apps.auth in INSTALLED_APPS")

    get_default_shop()
    prepare_user(regular_user)
    redirect_target = "/redirect-success/"
    response = client.post(reverse("shoop:login"), data={
        "username": regular_user.email,
        "password": REGULAR_USER_PASSWORD,
        REDIRECT_FIELD_NAME: redirect_target
    })

    assert response.get("location")
    assert response.get("location").endswith(redirect_target)

    request = rf.get("/")
    request.session = client.session
    assert get_user(request) == regular_user, "User is logged in"


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_login_with_email_2(client, regular_user, rf):
    if "shoop.front.apps.auth" not in settings.INSTALLED_APPS:
        pytest.skip("Need shoop.front.apps.auth in INSTALLED_APPS")

    # Create user with same email as regular user to fail login
    get_user_model().objects.create_user(
        username="el_person",
        password="123123",
        email=regular_user.email
    )

    get_default_shop()
    prepare_user(regular_user)
    redirect_target = "/redirect-success/"
    client.post(reverse("shoop:login"), data={
        "username": regular_user.email,
        "password": REGULAR_USER_PASSWORD,
        REDIRECT_FIELD_NAME: redirect_target
    })

    request = rf.get("/")
    request.session = client.session
    assert get_user(request).is_anonymous(), "User is still anonymous"

    # Login with unknown email
    client.post(reverse("shoop:login"), data={
        "username": "unknown@example.com",
        "password": REGULAR_USER_PASSWORD,
        REDIRECT_FIELD_NAME: redirect_target
    })

    request = rf.get("/")
    request.session = client.session
    assert get_user(request).is_anonymous(), "User is still anonymous"

    # Login with username should work normally
    response = client.post(reverse("shoop:login"), data={
        "username": regular_user.username,
        "password": REGULAR_USER_PASSWORD,
        REDIRECT_FIELD_NAME: redirect_target
    })

    assert response.get("location")
    assert response.get("location").endswith(redirect_target)

    request = rf.get("/")
    request.session = client.session
    assert get_user(request) == regular_user, "User is logged in"


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_login_with_email_3(client, regular_user, rf):
    if "shoop.front.apps.auth" not in settings.INSTALLED_APPS:
        pytest.skip("Need shoop.front.apps.auth in INSTALLED_APPS")

    new_user_password = "123123"
    new_user = get_user_model().objects.create_user(
        username=regular_user.email,
        password=new_user_password,
        email=regular_user.email
    )

    get_default_shop()
    prepare_user(regular_user)
    redirect_target = "/redirect-success/"

    # Login with new_user username should work even if there is users with same email
    response = client.post(reverse("shoop:login"), data={
        "username": regular_user.email,
        "password": new_user_password,
        REDIRECT_FIELD_NAME: redirect_target
    })

    assert response.get("location")
    assert response.get("location").endswith(redirect_target)

    request = rf.get("/")
    request.session = client.session
    assert get_user(request) == new_user, "User is logged in"
