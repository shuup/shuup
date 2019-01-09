# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json
from decimal import Decimal

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from shuup.core import cache
from shuup.core.api.front_orders import sum_order_lines_price
from shuup.core.models import get_person_contact, OrderLine, OrderLineType
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

    for (index, line) in enumerate(order.lines.filter(type=OrderLineType.PRODUCT)):
        line.base_unit_price_value = Decimal(index + 1)
        line.save()

    order.save()

    response = client.get("/api/shuup/front/orders/{}/".format(order.pk))
    response_data = json.loads(response.content.decode("utf-8"))
    assert response.status_code == status.HTTP_200_OK
    assert response_data["id"] == order.pk

    order.refresh_from_db()
    taxful_total_of_products = sum([line.price.value for line in order.lines.filter(type=OrderLineType.PRODUCT)])
    taxless_total_of_products = sum([line.taxless_price.value for line in order.lines.filter(type=OrderLineType.PRODUCT)])
    assert Decimal(response_data["taxful_total_price"]) == Decimal(order.taxful_total_price)
    assert Decimal(response_data["total_price_of_products"]) == Decimal(taxful_total_of_products)
    assert Decimal(response_data["taxful_total_price_of_products"]) == Decimal(taxful_total_of_products)  # prices include tax
    assert Decimal(response_data["taxless_total_price_of_products"]) == Decimal(taxless_total_of_products)
    assert Decimal(response_data["taxful_total_discount"]) == Decimal(0)

    # add shipping
    OrderLine.objects.create(
        text="Shipping",
        order=order,
        type=OrderLineType.SHIPPING,
        ordering=order.lines.count(),
        base_unit_price_value=Decimal(5),
        quantity=1
    )
    # add discount
    OrderLine.objects.create(
        text="Discount",
        order=order,
        type=OrderLineType.DISCOUNT,
        ordering=order.lines.count(),
        discount_amount_value=Decimal(2),
        quantity=1
    )

    order.save()
    order.refresh_from_db()

    response = client.get("/api/shuup/front/orders/{}/".format(order.pk))
    response_data = json.loads(response.content.decode("utf-8"))
    assert response.status_code == status.HTTP_200_OK
    assert response_data["id"] == order.pk

    total_of_products = sum([line.price.value for line in order.lines.filter(type=OrderLineType.PRODUCT)])
    assert Decimal(response_data["taxful_total_price"]) == Decimal(order.taxful_total_price)
    assert Decimal(response_data["total_price_of_products"]) == Decimal(total_of_products)
    assert Decimal(response_data["taxful_total_discount"]) == Decimal(2)

    assert Decimal(sum_order_lines_price(order, "price", lambda line: line.type == OrderLineType.SHIPPING)) == Decimal(5)

    response = client.get("/api/shuup/front/orders/{}/".format(100))
    assert response.status_code == 404

    response = client.get("/api/shuup/front/orders/{}/".format(order2.pk))
    assert response.status_code == 404


def _get_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client
