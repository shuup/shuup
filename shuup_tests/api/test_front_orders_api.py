# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json

import pytest
from rest_framework import status
from rest_framework.test import APIClient, force_authenticate
from shuup.core import cache
from shuup.core.models import get_person_contact
from shuup.testing.factories import (
    create_product, create_random_order, create_random_person,
    get_default_shop, get_default_supplier
)


def setup_function(fn):
    cache.clear()


@pytest.mark.django_db
def test_list_no_orders(admin_user):
    get_default_shop()
    client = _get_client(admin_user)
    response = client.get("/api/shuup/front/orders/")
    response_data = json.loads(response.content.decode("utf-8"))
    assert response.status_code == status.HTTP_200_OK
    assert len(response_data) == 0


@pytest.mark.django_db
def test_list_orders(admin_user):
    shop = get_default_shop()
    product = create_product("test", shop, get_default_supplier())
    order = create_random_order(get_person_contact(admin_user), [product])
    order2 = create_random_order(create_random_person(), [product])
    client = _get_client(admin_user)
    response = client.get("/api/shuup/front/orders/")
    response_data = json.loads(response.content.decode("utf-8"))
    assert response.status_code == status.HTTP_200_OK
    assert len(response_data) == 1
    assert "shop" in response_data[0]
    assert "contact_address" in response_data[0]["shop"]


@pytest.mark.django_db
def test_retrieve_order(admin_user):
    shop = get_default_shop()
    product = create_product("test", shop, get_default_supplier())
    order = create_random_order(get_person_contact(admin_user), [product])
    order2 = create_random_order(create_random_person(), [product])
    client = _get_client(admin_user)
    response = client.get("/api/shuup/front/orders/{}/".format(order.pk))
    response_data = json.loads(response.content.decode("utf-8"))
    assert response.status_code == status.HTTP_200_OK
    assert response_data["id"] == order.pk

    response = client.get("/api/shuup/front/orders/{}/".format(100))
    assert response.status_code == 404

    response = client.get("/api/shuup/front/orders/{}/".format(order2.pk))
    assert response.status_code == 404


def _get_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client
