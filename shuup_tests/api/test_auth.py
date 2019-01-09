# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import base64
import json

from django.core.urlresolvers import reverse
from rest_framework.test import APIClient

from shuup.testing.factories import get_default_shop


def test_basic_authentication(admin_user):
    get_default_shop()
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION='Basic ' + base64.b64encode(b'admin:password').decode("ascii"))
    response = client.get("/api/shuup/order/")
    assert response.status_code == 200

    client.credentials(HTTP_AUTHORIZATION='Basic ' + base64.b64encode(b'admin:bad-password').decode("ascii"))
    response = client.get("/api/shuup/order/")
    assert response.status_code == 401


def test_session_authentication(admin_user):
    get_default_shop()
    client = APIClient()
    client.login(username=admin_user.username, password="password")
    response = client.get("/api/shuup/order/")
    assert response.status_code == 200
    client.logout()
    response = client.get("/api/shuup/order/")
    assert response.status_code == 401


def test_jwt_authentication(admin_user):
    get_default_shop()
    client = APIClient()
    response = client.post("/api/api-token-auth/", data={"username": admin_user.username, "password": "password"})
    token = json.loads(response.content.decode("utf-8"))["token"]
    client.credentials(HTTP_AUTHORIZATION="JWT %s" % token)
    response = client.get("/api/shuup/order/")
    assert response.status_code == 200

    response = response = client.post("/api/api-token-refresh/", data={"token": token})
    assert response.status_code == 200

    client.credentials(HTTP_AUTHORIZATION='JWT bad-token')
    response = client.get("/api/shuup/order/")
    assert response.status_code == 401
