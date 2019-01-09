# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json
import math

import babel
import pytest
from django.utils.translation import activate
from rest_framework import status
from rest_framework.test import APIClient

from shuup.core import cache
from shuup.core.models import Currency, MutableAddress, Shop, ShopStatus
from shuup.testing.factories import (
    create_product, create_random_order, create_random_person,
    get_default_shop, get_default_supplier
)
from shuup.utils.i18n import get_current_babel_locale


def setup_function(fn):
    cache.clear()


@pytest.mark.parametrize("currency, currency_decimals", [
    ("USD", 2),
    ("BRL", 2),
    ("GBP", 2),
    ("USD", 2),
    ("IDR", 0),
    ("LYD", 3)
])
def test_shop_api(admin_user, currency, currency_decimals):
    activate("en")
    default_shop = get_default_shop()
    client = APIClient()
    client.force_authenticate(user=admin_user)
    Currency.objects.get_or_create(code=currency, decimal_places=currency_decimals)

    shop_data = {
        "domain": "shuup.com",
        "status": ShopStatus.ENABLED.value,
        "owner": create_random_person().pk,
        "currency": currency,
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
    assert shop.currency == data["currency"]["code"]
    assert data["currency"]["symbol"] == babel.numbers.get_currency_symbol(shop.currency, get_current_babel_locale())
    assert data["currency"]["decimal_places"] == currency_decimals
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


def test_shop_distance(admin_user):
    activate("en")
    shop1 = get_default_shop()
    shop1.contact_address = MutableAddress.objects.create(
        name="Apple Infinite Loop",
        street="1 Infinite Loop",
        country="US",
        city="Cupertino",
        latitude=37.331667,
        longitude=-122.030146
    )
    shop1.save()

    shop2 = Shop.objects.create(status=ShopStatus.ENABLED)
    shop2.contact_address = MutableAddress.objects.create(
        name="Googleplex",
        street="1600 Amphitheatre Pkwy",
        country="US",
        city="Mountain View",
        latitude=37.422000,
        longitude=-122.084024
    )
    shop2.save()

    shop3 = Shop.objects.create(status=ShopStatus.ENABLED)
    shop3.contact_address = MutableAddress.objects.create(
        name="Linkedin",
        street="2029 Stierlin Ct",
        country="US",
        city="Mountain View",
        latitude=37.423272,
        longitude=-122.070570
    )
    shop3.save()

    # using this calculator:
    # http://www.movable-type.co.uk/scripts/latlong.html
    my_position_to_apple = 2.982
    my_position_to_google = 10.57
    my_position_to_linkedin = 10.57

    # YMCA
    my_position = (37.328330, -122.063612)

    client = APIClient()
    client.force_authenticate(user=admin_user)

    # fetch only apple - max distance = 5km
    response = client.get("/api/shuup/shop/?lat={0}&lng={1}&distance={2}".format(my_position[0], my_position[1], 5),
                          content_type="application/json")
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert len(data) == 1
    assert data[0]["id"] == shop1.id
    # precision of 5 meters
    assert math.fabs(data[0]["distance"] - my_position_to_apple) < 0.05

    # fetch all - max distance = 12km - order by distance DESC
    response = client.get("/api/shuup/shop/?lat={0}&lng={1}&distance={2}&ordering=-distance".format(my_position[0], my_position[1], 12),
                          content_type="application/json")
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert len(data) == 3
    assert data[0]["id"] == shop3.id
    assert data[1]["id"] == shop2.id
    assert data[2]["id"] == shop1.id
    assert math.fabs(data[0]["distance"] - my_position_to_linkedin) < 0.05
    assert math.fabs(data[1]["distance"] - my_position_to_google) < 0.05
    assert math.fabs(data[2]["distance"] - my_position_to_apple) < 0.05

    my_position = (37.328330, -122.063612)
    close_position = (37.328320, -122.063611)

    # create a very close shop
    shop4 = Shop.objects.create(status=ShopStatus.ENABLED)
    shop4.contact_address = MutableAddress.objects.create(
        name="Very Close Location",
        street="A Stret",
        country="US",
        city="City",
        latitude=close_position[0],
        longitude=close_position[1]
    )
    shop4.save()

    # fetch the close location - max distance = 1km
    response = client.get("/api/shuup/shop/?lat={0}&lng={1}&distance={2}".format(my_position[0], my_position[1], 1),
                          content_type="application/json")
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert len(data) == 1
    assert data[0]["id"] == shop4.id
    assert math.fabs(data[0]["distance"]) < 0.01
