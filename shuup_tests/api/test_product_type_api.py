# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json

from rest_framework import status
from rest_framework.test import APIClient

from shuup.core import cache
from shuup.core.models import ProductType
from shuup.testing.factories import (
    create_product, create_random_product_attribute, get_default_shop
)


def setup_function(fn):
    cache.clear()


def test_product_type_api(admin_user):
    get_default_shop()
    client = APIClient()
    client.force_authenticate(user=admin_user)

    product_type_data = {
        "translations": {
            "en": {
                "name": "type 1"
            }
        },
        "attributes": [
            create_random_product_attribute().pk,
            create_random_product_attribute().pk,
            create_random_product_attribute().pk
        ]
    }
    response = client.post("/api/shuup/product_type/",
                           content_type="application/json",
                           data=json.dumps(product_type_data))
    assert response.status_code == status.HTTP_201_CREATED
    product_type = ProductType.objects.first()
    assert product_type.name == product_type_data["translations"]["en"]["name"]
    assert set(product_type.attributes.all().values_list("pk", flat=True)) >= set(product_type_data["attributes"])

    product_type_data["translations"]["en"]["name"] = "name 2"
    product_type_data["attributes"] = [
        create_random_product_attribute().pk,
        create_random_product_attribute().pk,
        create_random_product_attribute().pk
    ]

    response = client.put("/api/shuup/product_type/%d/" % product_type.id,
                          content_type="application/json",
                          data=json.dumps(product_type_data))
    assert response.status_code == status.HTTP_200_OK
    product_type = ProductType.objects.first()
    assert product_type.name == product_type_data["translations"]["en"]["name"]
    assert set(product_type.attributes.all().values_list("pk", flat=True)) >= set(product_type_data["attributes"])

    response = client.get("/api/shuup/product_type/%d/" % product_type.id)
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert product_type.name == data["translations"]["en"]["name"]
    assert set(product_type.attributes.all().values_list("pk", flat=True)) >= set(product_type_data["attributes"])

    response = client.get("/api/shuup/product_type/")
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert product_type.name == data[0]["translations"]["en"]["name"]
    assert set(product_type.attributes.all().values_list("pk", flat=True)) >= set(data[0]["attributes"])

    # delete
    response = client.delete("/api/shuup/product_type/%d/" % product_type.id)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert ProductType.objects.count() == 0

    # create a product and relate it to a product type
    product_type = ProductType.objects.create(name="type")
    product = create_product("product with product_type", type=product_type)

    # deleting product type should set product type to null
    response = client.delete("/api/shuup/product_type/%d/" % product_type.id)
    assert response.status_code == 204
    product.refresh_from_db()
    assert product.type is None
