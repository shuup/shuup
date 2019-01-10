# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from shuup.core import cache
from shuup.core.models import Shipment
from shuup.testing.factories import (
    create_random_order, create_random_person, get_shop
)


def setup_function(fn):
    cache.clear()


@pytest.mark.django_db
def test_get_shipments(admin_user):
    client = _get_client(admin_user)
    shop1 = get_shop(True)
    shop2 = get_shop(True)
    customer1 = create_random_person()
    customer2 = create_random_person()
    order1 = create_random_order(customer1, shop=shop1, completion_probability=1)
    order2 = create_random_order(customer2, shop=shop1, completion_probability=1)
    order3 = create_random_order(customer1, shop=shop2, completion_probability=1)
    order4 = create_random_order(customer2, shop=shop1, completion_probability=1)

    # list shipments
    response = client.get("/api/shuup/shipment/")
    assert response.status_code == status.HTTP_200_OK
    shipment_data = json.loads(response.content.decode("utf-8"))
    assert len(shipment_data) == 4
    assert shipment_data[0]["id"] == order1.shipments.first().pk
    assert shipment_data[1]["id"] == order2.shipments.first().pk
    assert shipment_data[2]["id"] == order3.shipments.first().pk
    assert shipment_data[3]["id"] == order4.shipments.first().pk

    # get shipment by id
    response = client.get("/api/shuup/shipment/%s/" % order1.shipments.first().pk)
    assert response.status_code == status.HTTP_200_OK
    shipment_data = json.loads(response.content.decode("utf-8"))
    assert shipment_data["id"] == order1.shipments.first().pk
    assert shipment_data["order"] == order1.pk

    # get shipment by product
    product = order2.shipments.first().products.first()
    response = client.get("/api/shuup/shipment/?product=%s" % product.pk)
    assert response.status_code == status.HTTP_200_OK
    shipment_data = json.loads(response.content.decode("utf-8"))
    for ship in shipment_data:
        for ship_product in shipment_data["product"]:
            assert ship_product["id"] == product.pk
            assert ship_product["order"] == order2.pk

    # get shipment by order
    response = client.get("/api/shuup/shipment/?order=%s" % order3.pk)
    assert response.status_code == status.HTTP_200_OK
    shipment_data = json.loads(response.content.decode("utf-8"))
    for ship in shipment_data:
        assert ship["order"] == order3.pk

    # get shipment by shop
    response = client.get("/api/shuup/shipment/?shop=%s" % shop1.pk)
    assert response.status_code == status.HTTP_200_OK
    shipment_data = json.loads(response.content.decode("utf-8"))
    for ship in shipment_data:
        assert Shipment.objects.filter(pk=ship["id"], order__shop=shop1).exists()


def _get_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client
