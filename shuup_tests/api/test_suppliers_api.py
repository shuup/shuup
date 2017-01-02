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
from rest_framework.test import APIClient

from shuup.core.models import Shop, ShopProduct, StockBehavior, Supplier
from shuup.testing.factories import (
    create_product, get_default_shop, get_default_shop_product,
    get_default_supplier
)
from shuup_tests.simple_supplier.utils import get_simple_supplier


def create_simple_supplier(identifier):
    ident = "supplier_%s" % identifier
    return Supplier.objects.create(
        identifier=ident,
        name=ident,
        module_identifier="simple_supplier",
    )


@pytest.mark.django_db
def test_get_suppliers(admin_user):
    client = _get_client(admin_user)
    shop1 = Shop.objects.create()
    shop2 = Shop.objects.create()

    supplier1 = create_simple_supplier("supplier1")
    supplier2 = create_simple_supplier("supplier2")

    product1 = create_product("product 1")
    product1.stock_behavior = StockBehavior.STOCKED
    sp = ShopProduct.objects.create(product=product1, shop=shop1)
    sp = ShopProduct.objects.create(product=product1, shop=shop2)
    sp.suppliers.add(supplier1)
    sp.suppliers.add(supplier2)

    product2 = create_product("product 2")
    product2.stock_behavior = StockBehavior.STOCKED
    sp = ShopProduct.objects.create(product=product2, shop=shop1)
    sp = ShopProduct.objects.create(product=product2, shop=shop2)
    sp.suppliers.add(supplier1)

    product3 = create_product("product 3")
    product3.stock_behavior = StockBehavior.STOCKED
    sp = ShopProduct.objects.create(product=product3, shop=shop1)
    sp.suppliers.add(supplier2)

    # put some stock
    supplier1.adjust_stock(product1.pk, 100)
    supplier1.adjust_stock(product2.pk, 300)
    supplier2.adjust_stock(product1.pk, 110)
    supplier2.adjust_stock(product3.pk, 300)

    # list suppliers
    response = client.get("/api/shuup/supplier/")
    assert response.status_code == status.HTTP_200_OK
    supplier_data = json.loads(response.content.decode("utf-8"))
    assert len(supplier_data) == 2
    assert supplier_data[0]["id"] == supplier1.pk
    assert supplier_data[1]["id"] == supplier2.pk

    # get supplier by id
    response = client.get("/api/shuup/supplier/%s/" % supplier2.pk)
    assert response.status_code == status.HTTP_200_OK
    supplier_data = json.loads(response.content.decode("utf-8"))
    assert supplier_data["id"] == supplier2.pk
    assert supplier_data["type"] == supplier2.type.value

    # get stocks by supplier
    response = client.get("/api/shuup/supplier/%s/stock/" % supplier1.pk)
    assert response.status_code == status.HTTP_200_OK
    supplier_data = sorted(json.loads(response.content.decode("utf-8")),
                           key=lambda sup: sup["product"])

    assert supplier_data[0]["sku"] == product1.sku
    assert supplier_data[0]["product"] == product1.pk
    assert supplier_data[0]["physical_count"] == supplier1.get_stock_status(product1.pk).physical_count
    assert supplier_data[0]["logical_count"] == supplier1.get_stock_status(product1.pk).logical_count

    assert supplier_data[1]["sku"] == product2.sku
    assert supplier_data[1]["product"] == product2.pk
    assert supplier_data[1]["physical_count"] == supplier1.get_stock_status(product2.pk).physical_count
    assert supplier_data[1]["logical_count"] == supplier1.get_stock_status(product2.pk).logical_count

    # get stocks by supplier - filter by product id
    response = client.get("/api/shuup/supplier/%s/stock/?product=%d" % (supplier1.pk, product1.id))
    assert response.status_code == status.HTTP_200_OK
    supplier_data = json.loads(response.content.decode("utf-8"))
    assert len(supplier_data) == 1
    assert supplier_data[0]["sku"] == product1.sku
    assert supplier_data[0]["product"] == product1.pk
    assert supplier_data[0]["physical_count"] == supplier1.get_stock_status(product1.pk).physical_count
    assert supplier_data[0]["logical_count"] == supplier1.get_stock_status(product1.pk).logical_count

    # get stocks by supplier - filter by sku
    response = client.get("/api/shuup/supplier/%s/stock/?sku=%s" % (supplier1.pk, product2.sku))
    assert response.status_code == status.HTTP_200_OK
    supplier_data = json.loads(response.content.decode("utf-8"))
    assert len(supplier_data) == 1
    assert supplier_data[0]["sku"] == product2.sku
    assert supplier_data[0]["product"] == product2.pk
    assert supplier_data[0]["physical_count"] == supplier1.get_stock_status(product2.pk).physical_count
    assert supplier_data[0]["logical_count"] == supplier1.get_stock_status(product2.pk).logical_count


@pytest.mark.django_db
def test_adjust_stock(admin_user):
    get_default_shop()
    sp = get_default_shop_product()
    sp.stock_behavior = StockBehavior.STOCKED
    sp.save()
    client = _get_client(admin_user)
    supplier = get_default_supplier()
    simple_supplier = get_simple_supplier()
    # invalid type
    response = client.post("/api/shuup/supplier/%s/stock/" % supplier.pk, data={
        "product": sp.product.pk,
        "delta": 100,
        "type": 100
    })
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = json.loads(response.content.decode("utf-8"))
    assert "type" in data

    # invalid supplier
    response = client.post("/api/shuup/supplier/%s/stock/" % 100, data={
        "product": sp.product.pk,
        "delta": 100,
        "type": 100
    })
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # invalid product
    response = client.post("/api/shuup/supplier/%s/stock/" % supplier.pk, data={
        "product": 100,
        "delta": 100,
        "type": 1
    })
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = json.loads(response.content.decode("utf-8"))
    assert "product" in data

    # invalid delta
    response = client.post("/api/shuup/supplier/%s/stock/" % supplier.pk, data={
        "product": sp.product.pk,
        "delta": "not-a-number",
        "type": 1
    })
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = json.loads(response.content.decode("utf-8"))
    assert "delta" in data

    # adjust stock not implemented
    response = client.post("/api/shuup/supplier/%s/stock/" % supplier.pk, data={
        "product": sp.product.pk,
        "delta": 100,
        "type": 1
    })
    assert response.status_code == 400

    # add 100 to inventory
    response = client.post("/api/shuup/supplier/%s/stock/" % simple_supplier.pk, data={
        "product": sp.product.pk,
        "delta": 100,
        "type": 1
    })
    assert response.status_code == 201
    stock = simple_supplier.get_stock_status(sp.product.pk)
    assert stock.logical_count == 100
    assert stock.physical_count == 100


def _get_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client
