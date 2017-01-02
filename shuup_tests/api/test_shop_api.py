# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json

from django.utils.translation import activate
from rest_framework import status
from rest_framework.test import APIClient

from shuup.core import cache
from shuup.core.models import Shop, ShopStatus
from shuup.testing.factories import (
    create_product, create_random_order, create_random_person,
    get_default_shop, get_default_supplier
)


def setup_function(fn):
    cache.clear()


def test_shop_api(admin_user):
    activate("en")
    default_shop = get_default_shop()
    client = APIClient()
    client.force_authenticate(user=admin_user)

    shop_data = {
        "domain": "shuup.com",
        "status": ShopStatus.ENABLED.value,
        "owner": create_random_person().pk,
        "currency": "USD",
        "prices_include_tax": True,
        "maintenance_mode": False,
        "translations":{
            "en": {
                "name": "Store 1",
                "public_name": "Public Store 1"
            }
        }
    }
    response = client.post("/api/shuup/shop/",
                           content_type="application/json",
                           data=json.dumps(shop_data))
    assert response.status_code == status.HTTP_201_CREATED
    shop = Shop.objects.exclude(pk=default_shop.pk).first()
    assert shop.domain == shop_data["domain"]
    assert shop.status.value == shop_data["status"]
    assert shop.owner.pk == shop_data["owner"]
    assert shop.currency == shop_data["currency"]
    assert shop.maintenance_mode == shop_data["maintenance_mode"]
    assert shop.prices_include_tax == shop_data["prices_include_tax"]
    assert shop.name == shop_data["translations"]["en"]["name"]
    assert shop.public_name == shop_data["translations"]["en"]["public_name"]

    shop_data["domain"] = "cloud.shuup.com"
    response = client.put("/api/shuup/shop/%d/" % shop.id,
                          content_type="application/json",
                          data=json.dumps(shop_data))
    assert response.status_code == status.HTTP_200_OK
    shop = Shop.objects.exclude(pk=default_shop.pk).first()
    assert shop.domain == shop_data["domain"]

    response = client.get("/api/shuup/shop/%d/" % shop.id)
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert shop.domain == data["domain"]
    assert shop.status.value == data["status"]
    assert shop.owner.pk == data["owner"]
    assert shop.currency == data["currency"]
    assert shop.maintenance_mode == data["maintenance_mode"]
    assert shop.prices_include_tax == data["prices_include_tax"]
    assert shop.name == data["translations"]["en"]["name"]
    assert shop.public_name == data["translations"]["en"]["public_name"]

    response = client.get("/api/shuup/shop/")
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert shop.domain == data[1]["domain"]

    response = client.delete("/api/shuup/shop/%d/" % shop.id)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Shop.objects.count() == 1

    # shouldn't be possible to delete a shop with a related order
    product = create_product("product1", shop=default_shop, supplier=get_default_supplier())
    create_random_order(create_random_person(), [product], completion_probability=1, shop=default_shop)
    response = client.delete("/api/shuup/shop/%d/" % default_shop.id)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "This object can not be deleted because it is referenced by" in response.content.decode("utf-8")
    assert Shop.objects.count() == 1
