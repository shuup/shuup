# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json

from django.utils.translation import activate
from rest_framework import status
from rest_framework.test import APIClient

from shuup.core import cache
from shuup.core.models import (
    ProductMode, ProductVariationLinkStatus, ProductVariationResult,
    ProductVariationVariable, ProductVariationVariableValue, Shop, ShopProduct,
    StockBehavior, Supplier
)
from shuup.core.models._product_variation import get_all_available_combinations
from shuup.testing.factories import create_product, get_default_shop


def setup_function(fn):
    cache.clear()


def test_product_simple_variation(admin_user):
    client = _get_client(admin_user)

    shop1 = get_default_shop()
    shop2 = Shop.objects.create(identifier="shop2")

    product1 = create_product("product1", shop=shop1)
    product2 = create_product("product2", shop=shop1)
    product3 = create_product("product3", shop=shop1)
    product4 = create_product("product4", shop=shop2)  # this is from shop2
    assert product1.mode == product2.mode == product3.mode == product4.mode == ProductMode.NORMAL

    variation_data = {"products":[product2.pk, product3.pk, product4.pk]}
    response = client.post("/api/shuup/product/%d/simple_variation/" % product1.pk,
                           content_type="application/json",
                           data=json.dumps(variation_data))
    assert response.status_code == status.HTTP_201_CREATED
    product1.refresh_from_db()
    product2.refresh_from_db()
    product3.refresh_from_db()
    product4.refresh_from_db()
    assert product1.mode == ProductMode.SIMPLE_VARIATION_PARENT
    assert product2.mode == product3.mode == product4.mode == ProductMode.VARIATION_CHILD

    # delete variation of product2
    variation_data = {"products":[product2.pk]}
    response = client.delete("/api/shuup/product/%d/simple_variation/" % product1.pk,
                             content_type="application/json",
                             data=json.dumps(variation_data))
    assert response.status_code == status.HTTP_204_NO_CONTENT
    product1.refresh_from_db()
    product2.refresh_from_db()
    product3.refresh_from_db()
    product4.refresh_from_db()
    assert product1.mode == ProductMode.SIMPLE_VARIATION_PARENT
    assert product2.mode == ProductMode.NORMAL
    assert product3.mode == product4.mode == ProductMode.VARIATION_CHILD


def test_product_variable_variation_api(admin_user):
    client = _get_client(admin_user)
    shop = get_default_shop()
    product = create_product("product", shop=shop)
    assert product.mode == ProductMode.NORMAL

    # create
    variation_data = {"product": product.pk, "translations": {"en": {"name": "Complex Variation Variable"}}}
    response = client.post("/api/shuup/product_variation_variable/",
                           content_type="application/json",
                           data=json.dumps(variation_data))
    assert response.status_code == status.HTTP_201_CREATED
    product.refresh_from_db()
    assert product.mode == ProductMode.VARIABLE_VARIATION_PARENT
    assert ProductVariationVariable.objects.filter(product=product).count() == 1
    assert ProductVariationVariableValue.objects.filter(variable__product=product).count() == 0

    # fetch
    response = client.get("/api/shuup/product_variation_variable/%d/" % ProductVariationVariable.objects.first().pk)
    assert response.status_code == status.HTTP_200_OK
    variable_data = json.loads(response.content.decode("utf-8"))
    assert variable_data["translations"]["en"]["name"] == variation_data["translations"]["en"]["name"]

    # update
    variation_data = {"product": product.pk, "translations": {"en": {"name": "Complex Variation Variable MODIFIED"}}}
    response = client.put("/api/shuup/product_variation_variable/%d/" % ProductVariationVariable.objects.first().pk,
                          content_type="application/json",
                          data=json.dumps(variation_data))
    assert response.status_code == status.HTTP_200_OK
    product.refresh_from_db()
    assert product.mode == ProductMode.VARIABLE_VARIATION_PARENT
    assert ProductVariationVariable.objects.filter(product=product).count() == 1
    assert ProductVariationVariableValue.objects.filter(variable__product=product).count() == 0

    # list
    response = client.get("/api/shuup/product_variation_variable/")
    assert response.status_code == status.HTTP_200_OK
    variable_data = json.loads(response.content.decode("utf-8"))
    assert variable_data[0]["translations"]["en"]["name"] == variation_data["translations"]["en"]["name"]

     # delete
    response = client.delete("/api/shuup/product_variation_variable/%d/" % ProductVariationVariable.objects.first().pk)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert ProductVariationVariable.objects.count() == 0
    product.refresh_from_db()
    assert product.mode == ProductMode.NORMAL


def test_product_variable_variation_value_api(admin_user):
    activate("en")
    client = _get_client(admin_user)
    shop = get_default_shop()
    product = create_product("product", shop=shop)
    assert product.mode == ProductMode.NORMAL
    var = ProductVariationVariable.objects.create(name="Complex Variable", product=product)
    product.verify_mode()
    product.save()

    value_data1 = {
        "variable": var.pk,
        "translations": {"en": {"value": "A"}}
    }
    value_data2 = {
        "variable": var.pk,
        "translations": {"en": {"value": "B"}}
    }

    # create
    response = client.post("/api/shuup/product_variation_variable_value/",
                           content_type="application/json",
                           data=json.dumps(value_data1))
    assert response.status_code == status.HTTP_201_CREATED

    response = client.post("/api/shuup/product_variation_variable_value/",
                           content_type="application/json",
                           data=json.dumps(value_data2))
    assert response.status_code == status.HTTP_201_CREATED

    assert ProductVariationVariableValue.objects.filter(variable__product=product).count() == 2
    value1 = ProductVariationVariableValue.objects.first()
    value2 = ProductVariationVariableValue.objects.last()

    # fetch
    response = client.get("/api/shuup/product_variation_variable_value/%d/" % value1.pk)
    assert response.status_code == status.HTTP_200_OK
    variable_data = json.loads(response.content.decode("utf-8"))
    assert variable_data["translations"]["en"]["value"] == variable_data["translations"]["en"]["value"]

    # update
    value_data2["translations"]["en"]["value"] = "C"
    response = client.put("/api/shuup/product_variation_variable_value/%d/" % value2.pk,
                          content_type="application/json",
                          data=json.dumps(value_data2))
    assert response.status_code == status.HTTP_200_OK

    # list
    response = client.get("/api/shuup/product_variation_variable_value/")
    assert response.status_code == status.HTTP_200_OK
    variable_data = json.loads(response.content.decode("utf-8"))
    assert variable_data[0]["translations"]["en"]["value"] == value_data1["translations"]["en"]["value"]
    assert variable_data[1]["translations"]["en"]["value"] == value_data2["translations"]["en"]["value"]

     # delete
    response = client.delete("/api/shuup/product_variation_variable_value/%d/" % value2.pk)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert ProductVariationVariableValue.objects.count() == 1


def test_product_variable_variation_link(admin_user):
    activate("en")
    client = _get_client(admin_user)
    shop = get_default_shop()

    product1 = create_product("product1", shop=shop)
    product2 = create_product("product2", shop=shop)
    product3 = create_product("product3", shop=shop)

    assert product1.mode == ProductMode.NORMAL
    var = ProductVariationVariable.objects.create(name="Complex Variable", product=product1)
    ProductVariationVariableValue.objects.create(variable=var, value="Value A")
    ProductVariationVariableValue.objects.create(variable=var, value="Value B")
    product1.verify_mode()
    product1.save()

    # create the combinations
    combinations = list(get_all_available_combinations(product1))
    hash1 = combinations[0]["hash"] # this must be Complex Variable: Value A
    hash2 = combinations[1]["hash"] # this must be Complex Variable: Value B

    # link product1 <- product2
    linkage_data = {
        "product": product2.pk,
        "hash": hash1,
        "status": ProductVariationLinkStatus.VISIBLE.value
    }
    response = client.post("/api/shuup/product/%d/variable_variation/" % product1.pk,
                           content_type="application/json",
                           data=json.dumps(linkage_data))
    assert response.status_code == status.HTTP_201_CREATED

    # link product1 <- product3
    linkage_data = {
        "product": product3.pk,
        "hash": hash2,
        "status": ProductVariationLinkStatus.VISIBLE.value
    }
    response = client.post("/api/shuup/product/%d/variable_variation/" % product1.pk,
                           content_type="application/json",
                           data=json.dumps(linkage_data))
    assert response.status_code == status.HTTP_201_CREATED

    result1 = ProductVariationResult.objects.get(combination_hash=hash1)
    assert result1.product.pk == product1.pk
    assert result1.status.value == ProductVariationLinkStatus.VISIBLE.value
    assert result1.result.pk == product2.pk

    result2 = ProductVariationResult.objects.get(combination_hash=hash2)
    assert result2.product.pk == product1.pk
    assert result2.status.value == ProductVariationLinkStatus.VISIBLE.value
    assert result2.result.pk == product3.pk

    combinations = list(get_all_available_combinations(product1))
    assert combinations[0]["result_product_pk"] == product2.pk
    assert combinations[1]["result_product_pk"] == product3.pk

    # update
    linkage_data = {
        "product": product2.pk,
        "hash": hash2,
        "status": ProductVariationLinkStatus.INVISIBLE.value
    }
    response = client.put("/api/shuup/product/%d/variable_variation/" % product1.pk,
                          content_type="application/json",
                          data=json.dumps(linkage_data))
    assert response.status_code == status.HTTP_200_OK
    result2 = ProductVariationResult.objects.get(combination_hash=hash2)
    assert result2.product.pk == product1.pk
    assert result2.status.value == ProductVariationLinkStatus.INVISIBLE.value
    assert result2.result.pk == product2.pk

    # delete
    response = client.delete("/api/shuup/product/%d/variable_variation/" % product1.pk,
                             content_type="application/json",
                             data=json.dumps({"hash": hash2}))
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert ProductVariationResult.objects.count() == 1

    response = client.delete("/api/shuup/product/%d/variable_variation/" % product1.pk,
                             content_type="application/json",
                             data=json.dumps({"hash": hash1}))
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert ProductVariationResult.objects.count() == 0

    # delete something not existent
    response = client.delete("/api/shuup/product/%d/variable_variation/" % product1.pk,
                             content_type="application/json",
                             data=json.dumps({"hash": hash1}))
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # update not existent
    response = client.put("/api/shuup/product/%d/variable_variation/" % product1.pk,
                          content_type="application/json",
                          data=json.dumps(linkage_data))
    assert response.status_code == status.HTTP_404_NOT_FOUND


def _get_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client
