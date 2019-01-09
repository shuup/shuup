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
from shuup.core.models import SalesUnit
from shuup.testing.factories import create_product, get_default_shop


def setup_function(fn):
    cache.clear()


def test_sales_unit_api(admin_user):
    activate("en")
    get_default_shop()
    client = APIClient()
    client.force_authenticate(user=admin_user)

    sales_unit_data = {
        "translations": {
            "en": {"name": "Kilo", "symbol": "KG"}
        },
        "decimals": 2
    }
    response = client.post("/api/shuup/sales_unit/",
                           content_type="application/json",
                           data=json.dumps(sales_unit_data))
    assert response.status_code == status.HTTP_201_CREATED
    sales_unit = SalesUnit.objects.first()
    assert sales_unit.name == sales_unit_data["translations"]["en"]["name"]
    assert sales_unit.symbol == sales_unit_data["translations"]["en"]["symbol"]
    assert sales_unit.decimals == sales_unit_data["decimals"]

    sales_unit_data["translations"]["en"]["name"] = "Pound"
    sales_unit_data["translations"]["en"]["symbol"] = "PD"
    sales_unit_data["decimals"] = 3

    response = client.put("/api/shuup/sales_unit/%d/" % sales_unit.id,
                          content_type="application/json",
                          data=json.dumps(sales_unit_data))
    assert response.status_code == status.HTTP_200_OK
    sales_unit = SalesUnit.objects.first()
    assert sales_unit.name == sales_unit_data["translations"]["en"]["name"]
    assert sales_unit.symbol == sales_unit_data["translations"]["en"]["symbol"]
    assert sales_unit.decimals == sales_unit_data["decimals"]

    response = client.get("/api/shuup/sales_unit/%d/" % sales_unit.id)
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert sales_unit.name == data["translations"]["en"]["name"]
    assert sales_unit.symbol == data["translations"]["en"]["symbol"]
    assert sales_unit.decimals == data["decimals"]

    response = client.get("/api/shuup/sales_unit/")
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert sales_unit.name == data[0]["translations"]["en"]["name"]
    assert sales_unit.symbol == data[0]["translations"]["en"]["symbol"]
    assert sales_unit.decimals == data[0]["decimals"]

    response = client.delete("/api/shuup/sales_unit/%d/" % sales_unit.id)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert SalesUnit.objects.count() == 0

    # create a product and relate it to a sales unit
    sales_unit = SalesUnit.objects.create(name="Kilo", symbol="KG")
    product = create_product("product with sales unit", sales_unit=sales_unit)

    # shouldn't be possible to delete a sales_unit with a related product
    response = client.delete("/api/shuup/sales_unit/%d/" % sales_unit.id)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "This object can not be deleted because it is referenced by" in response.content.decode("utf-8")
