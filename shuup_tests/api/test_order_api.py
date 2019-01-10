# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import datetime
import decimal
import json

import pytest
from django.utils.timezone import datetime as dt
from rest_framework import status
from rest_framework.test import APIClient

from shuup.core import cache
from shuup.core.models import (
    Currency, Order, OrderStatus, PaymentStatus, ShippingStatus
)
from shuup.testing.factories import (
    create_default_order_statuses, create_empty_order, create_product,
    create_random_person, get_default_customer_group, get_default_payment_method,
    get_default_shipping_method, get_default_shop, get_default_supplier,
    get_default_tax,
)
from shuup_tests.utils import printable_gibberish


def setup_function(fn):
    cache.clear()


@pytest.mark.django_db
def test_get_by_id(admin_user):
    shop = get_default_shop()
    order = create_empty_order(shop=shop)
    order.save()

    client = _get_client(admin_user)
    response = client.get("/api/shuup/order/%s/" % order.id)
    assert response.status_code == status.HTTP_200_OK
    order_data = json.loads(response.content.decode("utf-8"))
    assert order_data.get("id") == order.id


@pytest.mark.django_db
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


@pytest.mark.django_db
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


@pytest.mark.django_db
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


@pytest.mark.parametrize("currency", ["USD", "BRL", "GBP", "USD", "IDR", "LYD", "CAD"])
def test_create_order(admin_user, currency):
    create_default_order_statuses()
    shop = get_default_shop()
    shop.currency = currency
    tax = get_default_tax()
    Currency.objects.get_or_create(code=currency, decimal_places=2)
    shop.save()
    sm = get_default_shipping_method()
    pm = get_default_payment_method()
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)
    default_group = get_default_customer_group()
    default_group.members.add(contact)
    account_manager = create_random_person(locale="en_US", minimum_name_comp_len=5)
    contact.account_manager = account_manager
    contact.save()

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
    assert order.currency == currency
    for idx, line in enumerate(order.lines.all()[:4]):
        assert line.quantity == decimal.Decimal(lines[idx].get("quantity"))
        assert line.base_unit_price_value == decimal.Decimal(lines[idx].get("base_unit_price_value", 0))
        assert line.discount_amount_value == decimal.Decimal(lines[idx].get("discount_amount_value", 0))

    # Test tax summary
    response_data = json.loads(response.content.decode("utf-8"))
    # Tax summary should not be present here
    assert "summary" not in response_data

    response = client.get('/api/shuup/order/{}/taxes/'.format(order.pk))
    assert response.status_code == status.HTTP_200_OK
    response_data = json.loads(response.content.decode("utf-8"))

    assert "lines" in response_data
    assert "summary" in response_data
    line_summary = response_data["lines"]
    summary = response_data["summary"]
    first_tax_summary = summary[0]

    assert int(first_tax_summary["tax_id"]) == tax.id
    assert first_tax_summary["tax_rate"] == tax.rate

    first_line_summary = line_summary[0]
    assert "tax" in first_line_summary

    response = client.get("/api/shuup/order/%s/" % order.id)
    assert response.status_code == status.HTTP_200_OK
    order_data = json.loads(response.content.decode("utf-8"))
    assert order_data.get("id") == order.id

    assert "available_shipping_methods" in order_data
    assert "available_payment_methods" in order_data

    assert order_data["available_payment_methods"][0]["id"] == pm.id
    assert order_data["available_shipping_methods"][0]["id"] == sm.id

    assert order.account_manager == account_manager
    assert order.customer_groups.count() == contact.groups.count()
    for group in order.customer_groups.all():
        assert contact.groups.filter(id=group.id).exists()

    assert order.tax_group is not None
    assert order.tax_group == contact.tax_group


def test_create_without_a_contact(admin_user):
    create_default_order_statuses()
    shop = get_default_shop()
    sm = get_default_shipping_method()
    pm = get_default_payment_method()
    assert not Order.objects.count()
    client = _get_client(admin_user)
    lines = [
        {"type": "other", "sku": "hello", "text": "A greeting", "quantity": 1, "base_unit_price_value": "3.5"},
    ]
    response = client.post("/api/shuup/order/", content_type="application/json", data=json.dumps({
        "shop": shop.pk,
        "customer": None,
        "shipping_method": sm.pk,
        "payment_method": pm.pk,
        "lines": lines
    }))
    assert response.status_code == 201
    assert Order.objects.count() == 1
    order = Order.objects.first()
    assert order.shop == shop
    assert order.customer == None
    assert order.creator == admin_user
    assert order.shipping_method == sm
    assert order.payment_method == pm
    assert order.billing_address == None
    assert order.shipping_address == None
    assert order.payment_status == PaymentStatus.NOT_PAID
    assert order.shipping_status == ShippingStatus.NOT_SHIPPED
    assert order.status == OrderStatus.objects.get_default_initial()
    assert order.taxful_total_price_value == decimal.Decimal(3.5)
    assert order.lines.count() == 3 # shipping line, payment line, 2 product lines, 2 other lines
    for idx, line in enumerate(order.lines.all()[:1]):
        assert line.quantity == decimal.Decimal(lines[idx].get("quantity"))
        assert line.base_unit_price_value == decimal.Decimal(lines[idx].get("base_unit_price_value", 0))
        assert line.discount_amount_value == decimal.Decimal(lines[idx].get("discount_amount_value", 0))


def test_order_create_without_default_address(admin_user):
    create_default_order_statuses()
    shop = get_default_shop()
    sm = get_default_shipping_method()
    pm = get_default_payment_method()
    contact = create_random_person(locale="en_US", minimum_name_comp_len=5)
    contact.default_billing_address = None
    contact.default_shipping_address = None
    contact.save()
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
    assert order.billing_address is None
    assert order.shipping_address is None
    assert order.payment_status == PaymentStatus.NOT_PAID
    assert order.shipping_status == ShippingStatus.NOT_SHIPPED
    assert order.status == OrderStatus.objects.get_default_initial()
    assert order.taxful_total_price_value == decimal.Decimal(10)
    assert order.lines.count() == 6 # shipping line, payment line, 2 product lines, 2 other lines
    for idx, line in enumerate(order.lines.all()[:4]):
        assert line.quantity == decimal.Decimal(lines[idx].get("quantity"))
        assert line.base_unit_price_value == decimal.Decimal(lines[idx].get("base_unit_price_value", 0))
        assert line.discount_amount_value == decimal.Decimal(lines[idx].get("discount_amount_value", 0))

def test_order_create_without_shipping_or_billing_method(admin_user):
    create_default_order_statuses()
    shop = get_default_shop()
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
        "customer": contact.pk,
        "lines": lines
    }))
    assert response.status_code == 201
    assert Order.objects.count() == 1
    order = Order.objects.first()
    assert order.shop == shop
    assert order.shipping_method is None
    assert order.payment_method is None
    assert order.customer == contact
    assert order.creator == admin_user
    assert order.billing_address == contact.default_billing_address.to_immutable()
    assert order.shipping_address == contact.default_shipping_address.to_immutable()
    assert order.payment_status == PaymentStatus.NOT_PAID
    assert order.shipping_status == ShippingStatus.NOT_SHIPPED
    assert order.status == OrderStatus.objects.get_default_initial()
    assert order.taxful_total_price_value == decimal.Decimal(10)
    assert order.lines.count() == 4 # 2 product lines, 2 other lines
    for idx, line in enumerate(order.lines.all()[:4]):
        assert line.quantity == decimal.Decimal(lines[idx].get("quantity"))
        assert line.base_unit_price_value == decimal.Decimal(lines[idx].get("base_unit_price_value", 0))
        assert line.discount_amount_value == decimal.Decimal(lines[idx].get("discount_amount_value", 0))


def test_complete_order(admin_user):
    shop = get_default_shop()
    order = create_empty_order(shop=shop)
    order.save()
    client = _get_client(admin_user)
    response = client.post("/api/shuup/order/%s/complete/" % order.pk)
    assert response.status_code == 200
    response = client.post("/api/shuup/order/%s/complete/" % order.pk)
    assert response.status_code == 400


def test_cancel_order(admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    order = create_empty_order(shop=shop)
    order.save()
    client = _get_client(admin_user)
    response = client.post("/api/shuup/order/%s/cancel/" % order.pk)
    assert response.status_code == 200
    response = client.post("/api/shuup/order/%s/cancel/" % order.pk)
    assert response.status_code == 400


def _get_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client
