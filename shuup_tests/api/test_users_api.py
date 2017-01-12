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
from rest_framework import status
from rest_framework.test import APIClient

from shuup.core import cache
from shuup.core.models import Gender, PersonContact
from shuup.testing.factories import get_default_shop, UserFactory


def setup_function(fn):
    cache.clear()


def test_get_by_pk(admin_user):
    get_default_shop()
    for i in range(0,10):
        UserFactory()

    user = UserFactory()
    client = _get_client(admin_user)
    response = client.get("/api/shuup/user/%s/" % user.id)
    assert response.status_code == status.HTTP_200_OK
    user_data = json.loads(response.content.decode("utf-8"))
    assert user_data.get("id") == user.id
    assert user_data.get("username") == user.username


def test_get_by_email(admin_user):
    get_default_shop()
    for i in range(0, 10):
        UserFactory()

    user = UserFactory()
    client = _get_client(admin_user)

    response = client.get("/api/shuup/user/", data={"email": user.email})
    assert response.status_code == status.HTTP_200_OK
    user_data = json.loads(response.content.decode("utf-8"))

    assert get_user_model().objects.filter(email=user.email).count() == len(user_data)
    assert user_data[0].get("id") == user.id
    assert user_data[0].get("email") == user.email
    assert user_data[0].get("username") == user.username



def test_register_api(admin_user):
    shop = get_default_shop()
    client = _get_client(admin_user)
    PersonContact.objects.all().delete()

    register_data = {
        "username": "goodusername",
        "password": "somepassword",
        "contact": {
            "phone": "312312312",
            "name": "A good name",
            "email": "goodemail@apitest.com.cz",
            "gender": Gender.OTHER.value,
            "billing_address": {
                "name": "Address 1",
                "country": "BR",
                "street": "Street 1",
                "city": "City 1"
            },
            "shipping_address": {
                "name": "Adress 2",
                "country": "US",
                "street": "Street 2",
                "city": "City 2"
            }
        }
    }
    response = client.post("/api/shuup/user/register/",
                           content_type="application/json",
                           data=json.dumps(register_data))
    assert response.status_code == status.HTTP_201_CREATED
    person = PersonContact.objects.first()

    assert person.user.username == register_data["username"]
    assert person.user.check_password(register_data["password"])

    assert person.phone == register_data["contact"]["phone"]
    assert person.name == register_data["contact"]["name"]
    assert person.email == register_data["contact"]["email"]

    assert person.default_billing_address.name == register_data["contact"]["billing_address"]["name"]
    assert person.default_billing_address.country == register_data["contact"]["billing_address"]["country"]
    assert person.default_billing_address.street == register_data["contact"]["billing_address"]["street"]
    assert person.default_billing_address.city == register_data["contact"]["billing_address"]["city"]

    assert person.default_shipping_address.name == register_data["contact"]["shipping_address"]["name"]
    assert person.default_shipping_address.country == register_data["contact"]["shipping_address"]["country"]
    assert person.default_shipping_address.street == register_data["contact"]["shipping_address"]["street"]
    assert person.default_shipping_address.city == register_data["contact"]["shipping_address"]["city"]

    # Try to register with same username
    register_data = {
        "username": "goodusername",
        "password": "somepassword",
        "contact": {
            "name": "Namer 2"
        }
    }
    response = client.post("/api/shuup/user/register/",
                           content_type="application/json",
                           data=json.dumps(register_data))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "A user with that username already exists" in response.content.decode("utf-8")

    # register with basic data
    register_data = {
        "username": "olduser",
        "password": "pwd2",
        "contact": {
            "name": "My Name"
        }
    }
    response = client.post("/api/shuup/user/register/",
                           content_type="application/json",
                           data=json.dumps(register_data))
    assert response.status_code == status.HTTP_201_CREATED
    person = PersonContact.objects.get(user__username=register_data["username"])
    assert person.user.username == register_data["username"]
    assert person.name == register_data["contact"]["name"]


def test_register_email_api(admin_user):
    get_default_shop()
    client = _get_client(admin_user)
    PersonContact.objects.all().delete()

    register_data = {
        "contact": {
            "name": "A good name"
        },
        "email": "myemail@email.com",
        "password": "somepassword"
    }
    response = client.post("/api/shuup/user/register/",
                           content_type="application/json",
                           data=json.dumps(register_data))
    assert response.status_code == status.HTTP_201_CREATED
    person = PersonContact.objects.first()
    assert person.name == register_data["contact"]["name"]
    assert person.user.username == register_data["email"]
    assert person.user.check_password(register_data["password"])

    # register with DUPLICATED email
    register_data = {
        "contact": {
            "name": "A good name 2"
        },
        "email": "myemail@email.com",
        "password": "somepasswordz"
    }
    response = client.post("/api/shuup/user/register/",
                           content_type="application/json",
                           data=json.dumps(register_data))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "User already exists" in response.content.decode("utf-8")

    # register with diff email - now ok
    register_data = {
        "contact": {
            "name": "Ma Name"
        },
        "password": "somepassword",
        "email": "myemail_new@email.com"
    }
    response = client.post("/api/shuup/user/register/",
                           content_type="application/json",
                           data=json.dumps(register_data))
    assert response.status_code == status.HTTP_201_CREATED
    person = PersonContact.objects.get(email=register_data["email"])
    assert person.name == register_data["contact"]["name"]
    assert person.user.username == register_data["email"]
    assert person.user.check_password(register_data["password"])


def _get_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client
