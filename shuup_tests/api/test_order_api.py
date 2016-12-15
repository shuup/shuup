# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import datetime
import decimal
import json

from django.utils.timezone import datetime as dt
from rest_framework import status
from rest_framework.test import APIClient

from shuup.core.models import Order, OrderStatus, PaymentStatus, ShippingStatus
from shuup.testing.factories import (
    create_default_order_statuses, create_empty_order,
    create_order_with_product, create_product, create_random_person,
    get_default_payment_method, get_default_shipping_method, get_default_shop,
    get_default_supplier
)
from shuup_tests.utils import printable_gibberish


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


def test_create_order(admin_user):
    create_default_order_statuses()
    shop = get_default_shop()
    sm = get_default_shipping_method()
    pm = get_default_payment_method()
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)
    product = create_product(
        sku=printable_gibberish(),
        supplier=get_default_supplier(),
        shop=shop
    )
    assert not Order.objects.count()
    client = _get_client(admin_user)
    lines = [
        {"type": "product", "product": product.id, "quantity": "1", "base_unit_price_value": "5.00"},
        {"type": "product", "product": product.id, "quantity": "2", "base_unit_price_value": "1.00", "discount_amount_value": "0.50"},
        {"type": "other", "sku": "hello", "text": "A greeting", "quantity": 1, "base_unit_price_value": "3.5"},
        {"type": "text", "text": "This was an order!", "quantity": 0},
    ]
    response = client.post("/api/shuup/order/", content_type="application/json", data=json.dumps({
        "shop": shop.pk,
        "shipping_method": sm.pk,
        "payment_method": pm.pk,
        "customer": contact.pk,
        "lines": lines
    }))
    assert response.status_code == 201
    assert Order.objects.count() == 1
    order = Order.objects.first()
    assert order.shop == shop
    assert order.shipping_method == sm
    assert order.payment_method == pm
    assert order.customer == contact
    assert order.creator == admin_user
    assert order.billing_address == contact.default_billing_address.to_immutable()
    assert order.shipping_address == contact.default_shipping_address.to_immutable()
    assert order.payment_status == PaymentStatus.NOT_PAID
    assert order.shipping_status == ShippingStatus.NOT_SHIPPED
    assert order.status == OrderStatus.objects.get_default_initial()
    assert order.taxful_total_price_value == decimal.Decimal(10)
    assert order.lines.count() == 6 # shipping line, payment line, 2 product lines, 2 other lines
    for idx, line in enumerate(order.lines.all()[:4]):
        assert line.quantity == decimal.Decimal(lines[idx].get("quantity"))
        assert line.base_unit_price_value == decimal.Decimal(lines[idx].get("base_unit_price_value", 0))
        assert line.discount_amount_value == decimal.Decimal(lines[idx].get("discount_amount_value", 0))


def test_complete_order(admin_user):
    shop = get_default_shop()
    order = create_empty_order(shop=shop)
    order.save()
    client = _get_client(admin_user)
    response = client.put("/api/shuup/order/%s/complete/" % order.pk)
    assert response.status_code == 200
    response = client.put("/api/shuup/order/%s/complete/" % order.pk)
    assert response.status_code == 400


def test_cancel_order(admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    order = create_empty_order(shop=shop)
    order.save()
    client = _get_client(admin_user)
    response = client.put("/api/shuup/order/%s/cancel/" % order.pk)
    assert response.status_code == 200
    response = client.put("/api/shuup/order/%s/cancel/" % order.pk)
    assert response.status_code == 400


def _get_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client
