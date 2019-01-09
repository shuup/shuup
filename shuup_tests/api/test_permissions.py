# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import json

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import (
    APIClient, APIRequestFactory, force_authenticate
)

from shuup import configuration as config
from shuup.api.permissions import make_permission_config_key, PermissionLevel
from shuup.core import cache
from shuup.core.api.users import UserViewSet
from shuup.testing.factories import get_default_shop, UserFactory


def setup_function(fn):
    cache.clear()


@pytest.mark.django_db
def test_api_permissions_anonymous():
    users = [UserFactory(), UserFactory(), UserFactory(), UserFactory()]
    get_default_shop()
    viewset = UserViewSet()
    client = _get_client()
    permission_key = make_permission_config_key(viewset)

    # set API disabled
    config.set(None, permission_key, PermissionLevel.DISABLED)
    assert client.get("/api/shuup/user/").status_code == status.HTTP_401_UNAUTHORIZED
    assert client.post("/api/shuup/user/", {"email": "xiloca@djsij.com"}).status_code == status.HTTP_401_UNAUTHORIZED

    # set API Public WRITE - access granted
    config.set(None, permission_key, PermissionLevel.PUBLIC_WRITE)
    response = client.get("/api/shuup/user/")
    assert response.status_code == status.HTTP_200_OK
    user_data = sorted(json.loads(response.content.decode("utf-8")), key=lambda u: u["id"])
    for ix, user in enumerate(user_data):
        assert users[ix].id == user["id"]
    # DELETE data too
    assert client.delete("/api/shuup/user/%d/" % users[-1].id).status_code == status.HTTP_204_NO_CONTENT
    users.pop()

    # set API Public READ - access granted to read
    config.set(None, permission_key, PermissionLevel.PUBLIC_READ)
    response = client.get("/api/shuup/user/")
    assert response.status_code == status.HTTP_200_OK
    user_data = sorted(json.loads(response.content.decode("utf-8")), key=lambda u: u["id"])
    for ix, user in enumerate(user_data):
        assert users[ix].id == user["id"]
    # DELETE data - nope, not a safe method
    assert client.delete("/api/shuup/user/%d/" % users[-1].id).status_code == status.HTTP_401_UNAUTHORIZED

    # set API authenticated readonly - no access
    config.set(None, permission_key, PermissionLevel.AUTHENTICATED_READ)
    assert client.get("/api/shuup/user/").status_code == status.HTTP_401_UNAUTHORIZED
    assert client.delete("/api/shuup/user/%d/" % users[-1].id).status_code == status.HTTP_401_UNAUTHORIZED

    # set API authenticated write - no access
    config.set(None, permission_key, PermissionLevel.AUTHENTICATED_WRITE)
    assert client.get("/api/shuup/user/").status_code == status.HTTP_401_UNAUTHORIZED
    assert client.delete("/api/shuup/user/%d/" % users[-1].id).status_code == status.HTTP_401_UNAUTHORIZED

    # set API admin only - not a chance
    config.set(None, permission_key, PermissionLevel.ADMIN)
    assert client.get("/api/shuup/user/").status_code == status.HTTP_401_UNAUTHORIZED
    assert client.put("/api/shuup/user/", user_data[0]).status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_api_permissions_authenticated_user():
    users = [UserFactory(), UserFactory(), UserFactory()]
    my_user = users[-1]
    get_default_shop()
    viewset = UserViewSet()
    client = _get_client(my_user)

    permission_key = make_permission_config_key(viewset)

    # set API disabled
    config.set(None, permission_key, PermissionLevel.DISABLED)
    assert client.get("/api/shuup/user/").status_code == status.HTTP_403_FORBIDDEN
    assert client.post("/api/shuup/user/", {"email": "xiloca@djsij.com"}).status_code == status.HTTP_403_FORBIDDEN

    # set API Public WRITE - access granted
    config.set(None, permission_key, PermissionLevel.PUBLIC_WRITE)
    response = client.get("/api/shuup/user/")
    assert response.status_code == status.HTTP_200_OK
    user_data = sorted(json.loads(response.content.decode("utf-8")), key=lambda u: u["id"])
    for ix, user in enumerate(user_data):
        assert users[ix].id == user["id"]
    # DELETE data too
    assert client.delete("/api/shuup/user/%d/" % users[-1].id).status_code == status.HTTP_204_NO_CONTENT
    users.pop()

    # set API Public READ - access granted
    config.set(None, permission_key, PermissionLevel.PUBLIC_READ)
    response = client.get("/api/shuup/user/")
    assert response.status_code == status.HTTP_200_OK
    user_data = sorted(json.loads(response.content.decode("utf-8")), key=lambda u: u["id"])
    for ix, user in enumerate(user_data):
        assert users[ix].id == user["id"]

    # DELETE data - nope, not a safe method
    assert client.delete("/api/shuup/user/%d/" % users[0].id).status_code == status.HTTP_403_FORBIDDEN

    # set API authenticated readonly - access only for readonly
    config.set(None, permission_key, PermissionLevel.AUTHENTICATED_READ)
    response = client.get("/api/shuup/user/")
    assert response.status_code == status.HTTP_200_OK
    user_data = sorted(json.loads(response.content.decode("utf-8")), key=lambda u: u["id"])
    for ix, user in enumerate(user_data):
        assert users[ix].id == user["id"]
    assert client.delete("/api/shuup/user/%d/" % users[0].id).status_code == status.HTTP_403_FORBIDDEN

    # set API authenticated write - access granted
    config.set(None, permission_key, PermissionLevel.AUTHENTICATED_WRITE)
    assert client.get("/api/shuup/user/").status_code == status.HTTP_200_OK
    assert client.delete("/api/shuup/user/%d/" % users[-1].id).status_code == status.HTTP_204_NO_CONTENT
    users.pop()

    # set API admin only - not a chance
    config.set(None, permission_key, PermissionLevel.ADMIN)
    assert client.get("/api/shuup/user/").status_code == status.HTTP_403_FORBIDDEN
    assert client.delete("/api/shuup/user/%d/" % users[0].id).status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_api_permissions_admin_user(admin_user):
    users = [admin_user, UserFactory(), UserFactory(), UserFactory(), UserFactory()]
    get_default_shop()
    viewset = UserViewSet()
    client = _get_client(admin_user)

    permission_key = make_permission_config_key(viewset)

    # set API disabled
    config.set(None, permission_key, PermissionLevel.DISABLED)
    assert client.get("/api/shuup/user/").status_code == status.HTTP_403_FORBIDDEN
    assert client.post("/api/shuup/user/", {"email": "xiloca@djsij.com"}).status_code == status.HTTP_403_FORBIDDEN

    # set API Public WRITE - access granted
    config.set(None, permission_key, PermissionLevel.PUBLIC_WRITE)
    response = client.get("/api/shuup/user/")
    assert response.status_code == status.HTTP_200_OK
    user_data = sorted(json.loads(response.content.decode("utf-8")), key=lambda u: u["id"])
    for ix, user in enumerate(user_data):
        assert users[ix].id == user["id"]
    # DELETE data too
    assert client.delete("/api/shuup/user/%d/" % users[-1].id).status_code == status.HTTP_204_NO_CONTENT
    users.pop()

    # set API Public READ - access granted
    config.set(None, permission_key, PermissionLevel.PUBLIC_READ)
    response = client.get("/api/shuup/user/")
    assert response.status_code == status.HTTP_200_OK
    user_data = sorted(json.loads(response.content.decode("utf-8")), key=lambda u: u["id"])
    for ix, user in enumerate(user_data):
        assert users[ix].id == user["id"]

    # DELETE data - YES
    assert client.delete("/api/shuup/user/%d/" % users[-1].id).status_code == status.HTTP_204_NO_CONTENT
    users.pop()

    # set API authenticated readonly - access only for readonly
    config.set(None, permission_key, PermissionLevel.AUTHENTICATED_READ)
    response = client.get("/api/shuup/user/")
    assert response.status_code == status.HTTP_200_OK
    user_data = sorted(json.loads(response.content.decode("utf-8")), key=lambda u: u["id"])
    for ix, user in enumerate(user_data):
        assert users[ix].id == user["id"]
    assert client.delete("/api/shuup/user/%d/" % users[-1].id).status_code == status.HTTP_204_NO_CONTENT
    users.pop()

    # set API authenticated write - access granted
    config.set(None, permission_key, PermissionLevel.AUTHENTICATED_WRITE)
    assert client.get("/api/shuup/user/").status_code == status.HTTP_200_OK
    assert client.delete("/api/shuup/user/%d/" % users[-1].id).status_code == status.HTTP_204_NO_CONTENT
    users.pop()

    # set API admin only - aaaww yess
    config.set(None, permission_key, PermissionLevel.ADMIN)
    assert client.get("/api/shuup/user/").status_code == status.HTTP_200_OK
    assert client.delete("/api/shuup/user/%d/" % users[-1].id).status_code == status.HTTP_204_NO_CONTENT

    # as we deleted all users, we have left with just one - us
    get_user_model().objects.count() == 1


def _get_client(user=None):
    client = APIClient()
    if user:
        client.force_authenticate(user=user)
    return client
