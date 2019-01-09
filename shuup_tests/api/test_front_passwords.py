
# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
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
from shuup.testing.factories import get_default_shop


@pytest.mark.django_db
def test_reset_authenticated_user_password(admin_user):
    get_default_shop()
    client = _get_client()
    client.force_authenticate(user=admin_user)
    data = json.dumps({
       "new_password1": "typo",
       "new_password2": "foobar",
       "password": "badpassword"
    })
    response = client.post("/api/shuup/front/password/", content_type="application/json", data=data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "do not match" in str(response.content)
    data = json.dumps({
       "new_password1": "foobar",
       "new_password2": "foobar",
       "password": "badpassword"
    })
    response = client.post("/api/shuup/front/password/", content_type="application/json", data=data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not admin_user.check_password("foobar")
    data = json.dumps({
       "new_password1": "foobar",
       "new_password2": "foobar",
       "password": "password"
    })
    response = client.post("/api/shuup/front/password/", content_type="application/json", data=data)
    assert response.status_code == status.HTTP_200_OK
    assert admin_user.check_password("foobar")


@pytest.mark.django_db
def test_reset_password_request(admin_user):
    get_default_shop()
    client = _get_client()
    configuration.set(None, "api_permission_FrontUserViewSet", PermissionLevel.PUBLIC_WRITE)
    register_data = {
        "email": "myemail@email.com",
        "password": "somepassword"
    }
    response = client.post(
        "/api/shuup/front/user/",
        content_type="application/json",
        data=json.dumps(register_data))

    assert response.status_code == status.HTTP_201_CREATED
    user = get_user_model().objects.filter(email=register_data.get("email")).first()
    assert user.check_password("somepassword")

    configuration.set(None, "api_permission_PasswordResetViewSet", PermissionLevel.PUBLIC_WRITE)
    response = client.post(
        "/api/shuup/front/password/reset/",
        content_type="application/json",
        data=json.dumps({"email": "bademail"}))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in json.loads(response.content.decode("utf-8"))

    response = client.post(
        "/api/shuup/front/password/reset/",
        content_type="application/json",
        data=json.dumps({"email": "myemail@email.com"}))

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert len(mail.outbox) == 1
    content = mail.outbox[0].body
    url = content[content.find("http"):]
    _, _, _, _, uid, token, _ = url.split("/")

    configuration.set(None, "api_permission_SetPasswordViewSet", PermissionLevel.PUBLIC_WRITE)
    response = client.post(
        "/api/shuup/front/password/",
        content_type="application/json",
        data=json.dumps({
            "new_password1": "foobar",
            "new_password2": "foobar",
            "token": token,
            "uidb64": uid
        }))
    assert response.status_code == status.HTTP_200_OK
    user = get_user_model().objects.filter(email="myemail@email.com").first()
    assert user.check_password("foobar")


def _get_client():
    return APIClient()
