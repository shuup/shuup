# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import datetime
import json

from django.utils.timezone import datetime as dt
from rest_framework.test import APIClient
from rest_framework import status

from shuup.core.models import OrderStatus
from shuup.testing.factories import (
    create_default_order_statuses, create_empty_order, get_default_shop
)


def test_get_by_id(admin_user):
    shop = get_default_shop()
    order = create_empty_order(shop=shop)
    order.save()

    client = _get_client(admin_user)
    response = client.get("/api/shuup/order/%s/" % order.id)
    assert response.status_code == status.HTTP_200_OK
    order_data = json.loads(response.content.decode("utf-8"))
    assert order_data.get("id") == order.id


def test_get_by_identifier(admin_user):
    shop = get_default_shop()
    for i in range(1,10):
        order = create_empty_order(shop=shop)
        order.save()

    order = create_empty_order(shop=shop)
    order.save()
    client = _get_client(admin_user)
    response = client.get("/api/shuup/order/", data={"identifier": order.identifier})
    assert response.status_code == status.HTTP_200_OK
    order_data = json.loads(response.content.decode("utf-8"))
    assert order_data[0].get("id") == order.id
    assert order_data[0].get("identifier") == order.identifier


def test_get_by_order_date(admin_user):
    shop = get_default_shop()
    today = dt.today()
    yesterday = dt.today() - datetime.timedelta(days=1)
    for i in range(1, 10):
        order = create_empty_order(shop=shop)
        order.order_date = yesterday
        order.save()

    order = create_empty_order(shop=shop)
    order.save()
    client = _get_client(admin_user)
    response = client.get("/api/shuup/order/", data={"date": today})
    assert response.status_code == status.HTTP_200_OK
    order_data = json.loads(response.content.decode("utf-8"))

    assert len(order_data) == 1
    assert order_data[0].get("id") == order.id
    assert order_data[0].get("identifier") == order.identifier

    response = client.get("/api/shuup/order/", data={"date": yesterday})
    assert response.status_code == status.HTTP_200_OK
    order_data = json.loads(response.content.decode("utf-8"))
    assert len(order_data) == 9


def test_get_by_status(admin_user):
    create_default_order_statuses()
    shop = get_default_shop()
    cancelled_status = OrderStatus.objects.get_default_canceled()
    for i in range(1, 10):
        order = create_empty_order(shop=shop)
        order.status = cancelled_status
        order.save()

    order = create_empty_order(shop=shop)
    order.save()
    client = _get_client(admin_user)
    response = client.get("/api/shuup/order/", data={"status": order.status.id})
    assert response.status_code == status.HTTP_200_OK
    order_data = json.loads(response.content.decode("utf-8"))

    assert len(order_data) == 1
    assert order_data[0].get("id") == order.id
    assert order_data[0].get("identifier") == order.identifier

    response = client.get("/api/shuup/order/", data={"status": cancelled_status.id})
    assert response.status_code == status.HTTP_200_OK
    order_data = json.loads(response.content.decode("utf-8"))
    assert len(order_data) == 9

    assert order.can_set_complete()
    old_status = order.status
    order.status = OrderStatus.objects.get_default_complete()
    order.save()

    assert old_status != order.status
    response = client.get("/api/shuup/order/", data={"status": old_status.id})
    assert response.status_code == status.HTTP_200_OK
    order_data = json.loads(response.content.decode("utf-8"))
    assert len(order_data) == 0

    response = client.get("/api/shuup/order/", data={"status": order.status.id})
    assert response.status_code == status.HTTP_200_OK
    order_data = json.loads(response.content.decode("utf-8"))
    assert len(order_data) == 1


def _get_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client
