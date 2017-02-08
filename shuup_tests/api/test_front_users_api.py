# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json

from django.contrib.auth import get_user_model
from django.core import mail

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from shuup import configuration
from shuup.api.permissions import PermissionLevel
from shuup.core import cache
from shuup.core.models import Gender, PersonContact
from shuup.front.apps.registration.api import FrontUserViewSet
from shuup.testing.factories import get_default_shop, UserFactory


@pytest.mark.django_db
def test_register_api():
    shop = get_default_shop()
    configuration.set(None, "api_permission_FrontUserViewSet", PermissionLevel.PUBLIC_WRITE)
    client = _get_client()
    register_data = {
        "username": "goodusername",
        "password": "somepassword"
    }
    response = client.post("/api/shuup/front/user/",
                           content_type="application/json",
                           data=json.dumps(register_data))
    assert response.status_code == status.HTTP_201_CREATED
    response_json = json.loads(response.content.decode("utf-8"))
    assert "token" in response_json
    assert get_user_model().objects.count() == 1

    # Try to register with same username
    register_data = {
        "username": "goodusername",
        "password": "somepassword"
    }
    response = client.post("/api/shuup/front/user/",
                           content_type="application/json",
                           data=json.dumps(register_data))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "A user with that username already exists" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_register_email_api():
    get_default_shop()
    client = _get_client()
    register_data = {
        "email": "myemail@email.com",
        "password": "somepassword"
    }
    response = client.post("/api/shuup/front/user/",
                           content_type="application/json",
                           data=json.dumps(register_data))
    assert response.status_code == status.HTTP_201_CREATED
    response_json = json.loads(response.content.decode("utf-8"))
    assert "token" in response_json
    assert get_user_model().objects.count() == 1

    # register with DUPLICATED email
    register_data = {
        "email": "myemail@email.com",
        "password": "somepasswordz"
    }
    response = client.post("/api/shuup/front/user/",
                           content_type="application/json",
                           data=json.dumps(register_data))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "User already exists" in response.content.decode("utf-8")
    assert get_user_model().objects.count() == 1

    # register with diff email - now ok
    register_data = {
        "password": "somepassword",
        "email": "myemail_new@email.com"
    }
    response = client.post("/api/shuup/front/user/",
                           content_type="application/json",
                           data=json.dumps(register_data))
    assert response.status_code == status.HTTP_201_CREATED
    response_json = json.loads(response.content.decode("utf-8"))
    assert "token" in response_json
    assert get_user_model().objects.count() == 2


@pytest.mark.django_db
def test_register_bad_data():
    get_default_shop()
    client = _get_client()
    # no username or email
    register_data = {
        "password": "somepassword"
    }
    response = client.post("/api/shuup/front/user/",
                           content_type="application/json",
                           data=json.dumps(register_data))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "username and/or email is required" in response.content.decode("utf-8")

    # invalid email
    register_data = {
        "email": "invalidemail",
        "password": "somepassword"
    }
    response = client.post("/api/shuup/front/user/",
                           content_type="application/json",
                           data=json.dumps(register_data))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Enter a valid email address" in response.content.decode("utf-8")

    # no password
    register_data = {
        "email": "test@foo.com",
    }
    response = client.post("/api/shuup/front/user/",
                           content_type="application/json",
                           data=json.dumps(register_data))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "password" in json.loads(response.content.decode("utf-8"))


@pytest.mark.django_db
def test_reset_password_request():
    get_default_shop()
    client = _get_client()
    register_data = {
        "email": "myemail@email.com",
        "password": "somepassword"
    }
    client.post("/api/shuup/front/user/",
                content_type="application/json",
                data=json.dumps(register_data))
    user = get_user_model().objects.first()
    assert user.check_password("somepassword")
    configuration.set(None, "api_permission_PasswordResetViewSet", PermissionLevel.PUBLIC_WRITE)
    response = client.post("/api/shuup/front/password/reset/",
                           content_type="application/json",
                           data=json.dumps({"email": "bademail"}))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in json.loads(response.content.decode("utf-8"))

    response = client.post("/api/shuup/front/password/reset/",
                           content_type="application/json",
                           data=json.dumps({"email": "myemail@email.com"}))
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert len(mail.outbox) == 1
    content = mail.outbox[0].body
    url = content[content.find("http"):]
    _, _, _, _, uid, token, _ = url.split("/")

    configuration.set(None, "api_permission_SetPasswordViewSet", PermissionLevel.PUBLIC_WRITE)
    response = client.post("/api/shuup/front/password/",
                           content_type="application/json",
                           data=json.dumps({
                               "new_password1": "foobar",
                               "new_password2": "foobar",
                               "token": token,
                               "uidb64": uid
                            }))
    assert response.status_code == status.HTTP_200_OK
    user = get_user_model().objects.first()
    assert user.check_password("foobar")


def _get_client():
    return APIClient()
