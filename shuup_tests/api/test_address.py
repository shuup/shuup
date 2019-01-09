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
from shuup.core.models import MutableAddress
from shuup.testing.factories import create_random_person, get_default_shop
from django.test.utils import override_settings


def setup_function(fn):
    activate("en")
    cache.clear()


def test_mutable_address_api(admin_user):
    get_default_shop()
    client = APIClient()
    client.force_authenticate(user=admin_user)

    mutable_address_data = {
        "name": "Address Name",
        "city": "City Name",
        "country": "US",
        "street": "Good Street"
    }
    response = client.post("/api/shuup/address/",
                           content_type="application/json",
                           data=json.dumps(mutable_address_data))
    assert response.status_code == status.HTTP_201_CREATED
    mutable_address = MutableAddress.objects.first()
    assert mutable_address.name == mutable_address_data["name"]
    assert mutable_address.city == mutable_address_data["city"]
    assert mutable_address.street == mutable_address_data["street"]
    assert mutable_address.country == mutable_address_data["country"]

    mutable_address_data["name"] = "Changed Name"
    mutable_address_data["street"] = "Changed Street"
    mutable_address_data["country"] = "BR"
    mutable_address_data["city"] = "Changed City"

    response = client.put("/api/shuup/address/%d/" % mutable_address.id,
                          content_type="application/json",
                          data=json.dumps(mutable_address_data))
    assert response.status_code == status.HTTP_200_OK
    mutable_address = MutableAddress.objects.first()
    assert mutable_address.name == mutable_address_data["name"]
    assert mutable_address.city == mutable_address_data["city"]
    assert mutable_address.street == mutable_address_data["street"]
    assert mutable_address.country == mutable_address_data["country"]

    response = client.get("/api/shuup/address/%d/" % mutable_address.id)
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert mutable_address.name == data["name"]
    assert mutable_address.city == data["city"]
    assert mutable_address.street == data["street"]
    assert mutable_address.country == data["country"]

    # change some data
    mutable_address_data = {
        "name": "Changed again",
    }
    response = client.patch("/api/shuup/address/%d/" % mutable_address.id,
                            content_type="application/json",
                            data=json.dumps(mutable_address_data))
    assert response.status_code == status.HTTP_200_OK
    mutable_address = MutableAddress.objects.first()
    assert mutable_address.name == mutable_address_data["name"]

    response = client.delete("/api/shuup/address/%d/" % mutable_address.id)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert MutableAddress.objects.count() == 0

    # create a person and relate it to the address
    mutable_address = MutableAddress.objects.create(**mutable_address_data)
    person = create_random_person()
    person.default_billing_address = mutable_address
    person.save()

    # shouldn't be possible to delete a mutable_address with a related person
    response = client.delete("/api/shuup/address/%d/" % mutable_address.id)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "This object can not be deleted because it is referenced by" in response.content.decode("utf-8")


def test_mutable_address_field_properties_settings_api(admin_user, settings):
    settings.SHUUP_ADDRESS_FIELD_PROPERTIES["postal_code"] = {"required": True}
    settings.SHUUP_ADDRESS_FIELD_PROPERTIES["street2"] = {"required": True}

    get_default_shop()
    client = APIClient()
    client.force_authenticate(user=admin_user)

    mutable_address_data = {
        "name": "Address Name",
        "city": "City Name",
        "country": "US",
        "street": "Good Street"
    }
    response = client.post("/api/shuup/address/",
                        content_type="application/json",
                        data=json.dumps(mutable_address_data))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_data = json.loads(response.content.decode("utf-8"))
    assert "postal_code" in response_data
    assert "street2" in response_data

    mutable_address_data = {
        "name": "Address Name",
        "city": "City Name",
        "country": "US",
        "street": "Good Street",
        "street2": "street2",
        "postal_code": "31232131"
    }
    response = client.post("/api/shuup/address/",
                        content_type="application/json",
                        data=json.dumps(mutable_address_data))
    assert response.status_code == status.HTTP_201_CREATED
    mutable_address = MutableAddress.objects.first()
    assert mutable_address.name == mutable_address_data["name"]
    assert mutable_address.city == mutable_address_data["city"]
    assert mutable_address.street == mutable_address_data["street"]
    assert mutable_address.country == mutable_address_data["country"]
    assert mutable_address.street2 == mutable_address_data["street2"]
    assert mutable_address.postal_code == mutable_address_data["postal_code"]

    del(settings.SHUUP_ADDRESS_FIELD_PROPERTIES["postal_code"])
    del(settings.SHUUP_ADDRESS_FIELD_PROPERTIES["street2"])
