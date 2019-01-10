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
from rest_framework import status
from rest_framework.test import APIClient

from shuup.core import cache
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


def _get_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client
