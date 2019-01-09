# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from decimal import Decimal

import json
import pytest

from rest_framework import status
from rest_framework.test import APIClient

from shuup.core.models import OrderLineType, PaymentStatus, StockBehavior
from shuup.simple_supplier.models import StockAdjustment
from shuup.testing.factories import (
    create_order_with_product, create_product,
    get_default_shop, get_default_supplier
)
from shuup.utils.money import Money
from shuup_tests.simple_supplier.utils import get_simple_supplier


@pytest.mark.django_db
def test_refunds(admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=10,
    )
    tax_rate = Decimal("0.1")
    taxless_base_unit_price = shop.create_price(200)
    order = create_order_with_product(product, supplier, 3, taxless_base_unit_price, tax_rate, shop=shop)
    order.payment_status = PaymentStatus.DEFERRED
    order.cache_prices()
    order.save()

    assert len(order.lines.all()) == 1
    assert order.can_create_refund()
    assert not order.has_refunds()

    client = _get_client(admin_user)

    # Refund first and the only order line in 3 parts
    refund_url = "/api/shuup/order/%s/create_refund/" % order.id
    product_line = order.lines.first()
    data = {
        "refund_lines": [{
            "line": product_line.id,
            "quantity": 1,
            "amount": (product_line.taxful_price.amount.value / 3),
            "restock_products": False
        }]
    }

    # First refund
    response = client.post(refund_url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    order.refresh_from_db()
    assert order.lines.count() == 2
    assert order.has_refunds()

    # Second refund
    response = client.post(refund_url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    order.refresh_from_db()
    assert order.lines.count() == 3
    assert order.can_create_refund()

    # Third refund
    response = client.post(refund_url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    order.refresh_from_db()
    assert order.lines.count() == 4
    assert not order.can_create_refund()
    assert not order.taxful_total_price.amount
    assert order.get_total_tax_amount() == Money(
        (order.taxful_total_price_value - order.taxless_total_price_value),
        order.currency)

    # Test error message
    response = client.post(refund_url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    error_msg = json.loads(response.content.decode("utf-8"))["error"]
    assert error_msg == "Order can not be refunded at the moment."


@pytest.mark.django_db
def test_refund_entire_order_without_restock(admin_user):
    shop = get_default_shop()
    supplier = get_simple_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=10,
        stock_behavior=StockBehavior.STOCKED
    )
    supplier.adjust_stock(product.id, 5)
    _check_stock_counts(supplier, product, 5, 5)

    order = create_order_with_product(product, supplier, 2, 200, Decimal("0.24"), shop=shop)
    order.payment_status = PaymentStatus.DEFERRED
    order.cache_prices()
    order.save()

    original_total_price = order.taxful_total_price
    _check_stock_counts(supplier, product, 5, 3)

    client = _get_client(admin_user)
    refund_url = "/api/shuup/order/%s/create_full_refund/" % order.id
    data = {"restock_products": False}
    response = client.post(refund_url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    order.refresh_from_db()

    # Confirm the refund was created with correct amount
    assert order.taxless_total_price.amount.value == 0
    assert order.taxful_total_price.amount.value == 0
    refund_line = order.lines.order_by("ordering").last()
    assert refund_line.type == OrderLineType.REFUND
    assert refund_line.taxful_price == -original_total_price

    # Make sure logical count reflects refunded products
    _check_stock_counts(supplier, product, 5, 3)


@pytest.mark.django_db
def test_refund_entire_order_with_restock(admin_user):
    shop = get_default_shop()
    supplier = get_simple_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=10,
        stock_behavior=StockBehavior.STOCKED
    )
    supplier.adjust_stock(product.id, 5)
    _check_stock_counts(supplier, product, 5, 5)

    order = create_order_with_product(product, supplier, 2, 200, shop=shop)
    order.payment_status = PaymentStatus.DEFERRED
    order.cache_prices()
    order.save()

    _check_stock_counts(supplier, product, 5, 3)
    assert not StockAdjustment.objects.filter(created_by=admin_user).exists()

    client = _get_client(admin_user)
    refund_url = "/api/shuup/order/%s/create_full_refund/" % order.id
    data = {"restock_products": True}
    response = client.post(refund_url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    order.refresh_from_db()

    # restock logical count
    _check_stock_counts(supplier, product, 5, 5)
    assert StockAdjustment.objects.filter(created_by=admin_user).exists()


@pytest.mark.django_db
def test_refund_errors(admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(
        "test-sku",
        shop=get_default_shop(),
        default_price=10,
    )
    tax_rate = Decimal("0.1")
    taxless_base_unit_price = shop.create_price(200)
    order = create_order_with_product(product, supplier, 3, taxless_base_unit_price, tax_rate, shop=shop)
    order.payment_status = PaymentStatus.DEFERRED
    order.cache_prices()
    order.save()

    assert len(order.lines.all()) == 1
    assert order.can_create_refund()
    assert not order.has_refunds()

    client = _get_client(admin_user)

    refund_url = "/api/shuup/order/%s/create_refund/" % order.id
    product_line = order.lines.first()

    # error 1 - max refundable limit
    data = {
        "refund_lines": [{
            "line": product_line.id,
            "quantity": 1000,
            "amount": 1,
            "restock_products": False
        }]
    }
    response = client.post(refund_url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Refund exceeds quantity." in response.data

    # error 2 - max amount
    data = {
        "refund_lines": [{
            "line": product_line.id,
            "quantity": 1,
            "amount": 100000000,
            "restock_products": False
        }]
    }
    response = client.post(refund_url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Refund exceeds amount." in response.data

    # error 3 - invalid amount
    data = {
        "refund_lines": [{
            "line": product_line.id,
            "quantity": 1,
            "amount": -10,
            "restock_products": False
        }]
    }
    response = client.post(refund_url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid refund amount." in response.data

    # create partial refund
    data = {
        "refund_lines": [{
            "line": product_line.id,
            "quantity": 1,
            "amount": 1,
            "restock_products": False
        }]
    }
    response = client.post(refund_url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED

    # error 4 - can't create full refund
    data = {"restock_products": False}
    response = client.post("/api/shuup/order/%s/create_full_refund/" % order.id, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "It is not possible to create the refund." in response.data


def _check_stock_counts(supplier, product, physical, logical):
    physical_count = supplier.get_stock_statuses([product.id])[product.id].physical_count
    logical_count = supplier.get_stock_statuses([product.id])[product.id].logical_count
    assert physical_count == physical
    assert logical_count == logical


def _get_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client
