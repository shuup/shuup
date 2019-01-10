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
from shuup.core.models import Order
from shuup.testing.factories import (
    create_order_with_product, get_default_product, get_default_shop,
    get_default_supplier
)


def setup_function(fn):
    cache.clear()


def create_order():
    shop = get_default_shop()
    product = get_default_product()
    supplier = get_default_supplier()
    order = create_order_with_product(
        product,
        shop=shop,
        supplier=supplier,
        quantity=1,
        taxless_base_unit_price=10,
    )
    order.cache_prices()
    order.save()
    return order


def get_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


def get_create_payment_url(order_pk):
    return "/api/shuup/order/%s/create_payment/" % order_pk


def get_set_fully_paid_url(order_pk):
    return "/api/shuup/order/%s/set_fully_paid/" % order_pk


def get_order_url(order_pk):
    return "/api/shuup/order/%s/" % order_pk


@pytest.mark.django_db
def test_create_payment(admin_user):
    order = create_order()
    client = get_client(admin_user)

    payment_identifier = "some_identifier"
    data = {
        "amount_value": 1,
        "payment_identifier": payment_identifier,
        "description": "some_payment"
    }

    response = client.post(
        get_create_payment_url(order.pk),
        data,
        format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert order.get_total_paid_amount().value == 1

    response = client.get(
        get_order_url(order.pk),
        format="json"
    )
    assert response.status_code == status.HTTP_200_OK
    order_data = json.loads(response.content.decode("utf-8"))
    payments = order_data["payments"]
    assert len(payments) == 1
    assert payments[0]["payment_identifier"] == payment_identifier


@pytest.mark.django_db
def test_set_fully_paid(admin_user):
    order = create_order()
    client = get_client(admin_user)
    data = {
        "payment_identifier": 1,
        "description": "some_payment"
    }
    order_pk = order.pk
    response = client.post(
        get_set_fully_paid_url(order_pk),
        data,
        format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED
    order = Order.objects.get(pk=order_pk)
    assert bool(order.is_paid())
    currently_paid_amount = order.get_total_paid_amount()

    # Make sure that api works with already fully paid orders
    response = client.post(
        "/api/shuup/order/%s/set_fully_paid/" % order_pk,
        data,
        format="json"
    )
    assert response.status_code == status.HTTP_200_OK
    order = Order.objects.get(pk=order_pk)
    assert bool(order.is_paid())
    assert currently_paid_amount == order.get_total_paid_amount()


@pytest.mark.django_db
def test_set_paid_from_partially_paid_order(admin_user):
    order = create_order()
    client = get_client(admin_user)

    data = {
        "amount_value": 1,
        "payment_identifier": 1,
        "description": "some_payment"
    }

    response = client.post(
        get_create_payment_url(order.pk),
        data,
        format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert order.get_total_paid_amount().value == 1

    data = {
        "payment_identifier": 2,
        "description": "some_payment"
    }
    order_pk = order.pk
    response = client.post(
        get_set_fully_paid_url(order_pk),
        data,
        format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED
    order = Order.objects.get(pk=order_pk)
    assert bool(order.is_paid())
    assert bool(order.get_total_paid_amount() == order.taxful_total_price.amount)
