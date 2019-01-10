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

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from shuup import configuration
from shuup.api.permissions import PermissionLevel
from shuup.core.models import Gender, PersonContact
from shuup.testing.factories import get_default_shop


@pytest.mark.django_db
def test_register_api():
    get_default_shop()
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
    assert "User already exists" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_register_email_api():
    get_default_shop()
    configuration.set(None, "api_permission_FrontUserViewSet", PermissionLevel.PUBLIC_WRITE)
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
    configuration.set(None, "api_permission_FrontUserViewSet", PermissionLevel.PUBLIC_WRITE)
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
def test_update_user(admin_user):
    get_default_shop()
    client = _get_client()

    # anonymous user
    configuration.set(None, "api_permission_FrontUserViewSet", PermissionLevel.PUBLIC_WRITE)
    response = client.put("/api/shuup/front/user/me/",
                          content_type="application/json",
                          data=json.dumps({"first_name": "derp"}))
    assert response.status_code == 404

    client.force_authenticate(user=admin_user)
    # set attributes on the person contact model only
    data = {
        "gender": Gender.MALE.value,
        "first_name": "derp"
    }

    response = client.put("/api/shuup/front/user/me/",
                          content_type="application/json",
                          data=json.dumps(data))
    response_data = json.loads(response.content.decode("utf-8"))
    assert response.status_code == 200
    assert response_data["first_name"] == "derp"
    assert response_data["gender"] == Gender.MALE.value
    assert PersonContact.objects.count() == 1
    contact = PersonContact.objects.first()
    assert contact.first_name == "derp"

    # set attributes on person contact and address models
    data = {
        "gender": Gender.FEMALE.value,
        "default_shipping_address": {
            "name": "Address Name",
            "city": "City Name",
            "country": "US",
            "street": "Good Street"
        }
    }
    response = client.put("/api/shuup/front/user/me/",
                          content_type="application/json",
                          data=json.dumps(data))
    response_data = json.loads(response.content.decode("utf-8"))
    assert response.status_code == 200
    assert response_data["default_shipping_address"]["name"] == "Address Name"
    assert PersonContact.objects.count() == 1
    contact = PersonContact.objects.first()
    assert contact.default_shipping_address
    assert contact.default_shipping_address.name == "Address Name"
    assert not contact.default_billing_address

    # update address fields
    data = {
        "default_shipping_address": {
            "name": "derp",
            "city": "City Name",
            "country": "US",
            "street": "Good Street"
        }
    }
    response = client.put("/api/shuup/front/user/me/",
                          content_type="application/json",
                          data=json.dumps(data))
    response_data = json.loads(response.content.decode("utf-8"))
    assert response.status_code == 200
    assert response_data["default_shipping_address"]["name"] == "derp"
    assert response_data["default_shipping_address"]["city"] == "City Name"
    contact = PersonContact.objects.first()
    assert contact.default_shipping_address.name == "derp"


def test_get_user(admin_user):
    get_default_shop()
    client = _get_client()
    client.force_authenticate(user=admin_user)
    response = client.get("/api/shuup/front/user/me/")
    response_data = json.loads(response.content.decode("utf-8"))
    assert response.status_code == 200
    assert "default_shipping_address" in response_data
    assert "first_name" in response_data


def _get_client():
    return APIClient()
