# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json

from rest_framework import status
from rest_framework.test import APIClient

from shuup.core import cache
from shuup.core.models import Shop, ShopProduct, StockBehavior, Supplier
from shuup.testing.factories import create_product, get_default_shop


def setup_function(fn):
    cache.clear()


def get_products_by_id_sku(admin_user):
    client = _get_client(admin_user)
    get_default_shop()
    products = [create_product("product 1"), create_product("product 2"), create_product("product 3")]
    client = _get_client(admin_user)

    # get by ID
    response = client.get("/api/shuup/product/?id=%d" % products[2].id)
    assert response.status_code == status.HTTP_200_OK
    product_data = json.loads(response.content.decode("utf-8"))
    assert len(product_data) == 1
    assert product_data[0]["product"] == products[2].id
    assert product_data[0]["sku"] == products[2].id

    # get by SKU
    response = client.get("/api/shuup/product/?sku=%s" % products[1].sku)
    assert response.status_code == status.HTTP_200_OK
    product_data = json.loads(response.content.decode("utf-8"))
    assert len(product_data) == 1
    assert product_data[0]["product"] == products[1].id
    assert product_data[0]["sku"] == products[1].id


def create_simple_supplier(identifier):
    ident = "supplier_%s" % identifier
    return Supplier.objects.create(
        identifier=ident,
        name=ident,
        module_identifier="simple_supplier",
    )


def test_get_product_stocks(admin_user):
    client = _get_client(admin_user)
    shop1 = Shop.objects.create()
    shop2 = Shop.objects.create()

    supplier1 = create_simple_supplier("1")
    supplier2 = create_simple_supplier("2")

    product1 = create_product("product 1")
    product1.stock_behavior = StockBehavior.STOCKED
    product1.save()
    sp = ShopProduct.objects.create(product=product1, shop=shop1)
    sp.suppliers.add(supplier1)
    sp.suppliers.add(supplier2)
    sp = ShopProduct.objects.create(product=product1, shop=shop2)
    sp.suppliers.add(supplier1)
    sp.suppliers.add(supplier2)

    product2 = create_product("product 2")
    product2.stock_behavior = StockBehavior.STOCKED
    product2.save()
    sp = ShopProduct.objects.create(product=product2, shop=shop1)
    sp.suppliers.add(supplier1)
    sp = ShopProduct.objects.create(product=product2, shop=shop2)
    sp.suppliers.add(supplier1)

    product3 = create_product("product 3", shop=shop1, supplier=supplier2)
    product3.stock_behavior = StockBehavior.STOCKED
    product3.save()

    # put some stock
    supplier1.adjust_stock(product1.pk, 100)
    supplier1.adjust_stock(product2.pk, 300)
    supplier2.adjust_stock(product1.pk, 110)
    supplier2.adjust_stock(product3.pk, 300)

    # list all stocks
    response = client.get("/api/shuup/product/stocks/")
    assert response.status_code == status.HTTP_200_OK
    stock_data = sorted(json.loads(response.content.decode("utf-8")),
                        key=lambda prod: prod["product"])
    assert len(stock_data) == 3

    assert stock_data[0]["product"] == product1.pk
    assert stock_data[0]["sku"] == product1.sku
    stocks = sorted(stock_data[0]["stocks"], key=lambda stock: stock["id"])
    assert len(stocks) == 2
    assert stocks[0]["id"] == supplier1.id
    assert stocks[0]["physical_count"] == supplier1.get_stock_status(product1.pk).physical_count
    assert stocks[0]["logical_count"] == supplier1.get_stock_status(product1.pk).logical_count
    assert stocks[1]["id"] == supplier2.id
    assert stocks[1]["physical_count"] == supplier2.get_stock_status(product1.pk).physical_count
    assert stocks[1]["logical_count"] == supplier2.get_stock_status(product1.pk).logical_count

    assert stock_data[1]["product"] == product2.pk
    assert stock_data[1]["sku"] == product2.sku
    stocks = sorted(stock_data[1]["stocks"], key=lambda stock: stock["id"])
    assert len(stocks) == 1
    assert stocks[0]["id"] == supplier1.id
    assert stocks[0]["physical_count"] == supplier1.get_stock_status(product2.pk).physical_count
    assert stocks[0]["logical_count"] == supplier1.get_stock_status(product2.pk).logical_count

    assert stock_data[2]["product"] == product3.pk
    assert stock_data[2]["sku"] == product3.sku
    stocks = sorted(stock_data[2]["stocks"], key=lambda stock: stock["id"])
    assert len(stocks) == 1
    assert stocks[0]["id"] == supplier2.id
    assert stocks[0]["physical_count"] == supplier2.get_stock_status(product3.pk).physical_count
    assert stocks[0]["logical_count"] == supplier2.get_stock_status(product3.pk).logical_count

    # list all stocks - filter by supplier and sku
    response = client.get("/api/shuup/product/stocks/?sku=%s&supplier=%d" % (product1.sku, supplier1.id))
    assert response.status_code == status.HTTP_200_OK
    stock_data = sorted(json.loads(response.content.decode("utf-8")),
                        key=lambda prod: prod["product"])
    assert len(stock_data) == 1
    assert stock_data[0]["product"] == product1.pk
    assert stock_data[0]["sku"] == product1.sku
    assert stock_data[0]["stocks"][0]["id"] == supplier1.id
    assert stock_data[0]["stocks"][0]["physical_count"] == supplier1.get_stock_status(product1.pk).physical_count
    assert stock_data[0]["stocks"][0]["logical_count"] == supplier1.get_stock_status(product1.pk).logical_count

    # list all stocks - filter by supplier and id
    response = client.get("/api/shuup/product/stocks/?product=%d&supplier=%d" % (product2.id, supplier1.id))
    assert response.status_code == status.HTTP_200_OK
    stock_data = sorted(json.loads(response.content.decode("utf-8")),
                        key=lambda prod: prod["product"])
    assert len(stock_data) == 1
    assert stock_data[0]["product"] == product2.pk
    assert stock_data[0]["sku"] == product2.sku
    assert stock_data[0]["stocks"][0]["id"] == supplier1.id
    assert stock_data[0]["stocks"][0]["physical_count"] == supplier1.get_stock_status(product2.pk).physical_count
    assert stock_data[0]["stocks"][0]["logical_count"] == supplier1.get_stock_status(product2.pk).logical_count


def _get_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client
