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

from django.utils.translation import activate
from rest_framework import status
from rest_framework.test import APIClient

from shuup.core import cache
from shuup.customer_group_pricing.models import CgpPrice
from shuup.testing.factories import (
    create_product, get_default_customer_group, get_default_shop
)


def setup_function(fn):
    cache.clear()


def test_cgp_price_api(admin_user):
    activate("en")
    shop = get_default_shop()
    client = APIClient()
    client.force_authenticate(user=admin_user)
    product1 = create_product("product1", shop=shop)
    product2 = create_product("product2", shop=shop)
    group = get_default_customer_group()

    cgp_price_data = {
        "product": product1.pk,
        "shop": shop.pk,
        "group": group.pk,
        "price_value": 15.0
    }

    # create
    response = client.post("/api/shuup/cgp_price/",
                           content_type="application/json",
                           data=json.dumps(cgp_price_data))
    assert response.status_code == status.HTTP_201_CREATED
    cgp_price = CgpPrice.objects.first()
    assert cgp_price.product.pk == cgp_price_data["product"]
    assert cgp_price.shop.pk == cgp_price_data["shop"]
    assert cgp_price.group.pk == cgp_price_data["group"]
    assert cgp_price.price_value == Decimal(cgp_price_data["price_value"])

    # update
    cgp_price_data["product"] = product2.pk
    response = client.put("/api/shuup/cgp_price/%d/" % cgp_price.id,
                          content_type="application/json",
                          data=json.dumps(cgp_price_data))
    assert response.status_code == status.HTTP_200_OK
    cgp_price = CgpPrice.objects.first()
    assert cgp_price.product.pk == cgp_price_data["product"]

    # fetch
    response = client.get("/api/shuup/cgp_price/%d/" % cgp_price.id)
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert cgp_price.product.pk == data["product"]
    assert cgp_price.shop.pk == data["shop"]
    assert cgp_price.group.pk == data["group"]
    assert cgp_price.price_value == Decimal(data["price_value"])

    # list
    response = client.get("/api/shuup/cgp_price/")
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert cgp_price.product.pk == data[0]["product"]
    assert cgp_price.shop.pk == data[0]["shop"]
    assert cgp_price.group.pk == data[0]["group"]
    assert cgp_price.price_value == Decimal(data[0]["price_value"])

    # delete
    response = client.delete("/api/shuup/cgp_price/%d/" % cgp_price.id)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert CgpPrice.objects.count() == 0
