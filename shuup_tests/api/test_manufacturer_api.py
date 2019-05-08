# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json
import base64
import os
from rest_framework import status
from rest_framework.test import APIClient

from shuup.core import cache
from shuup.core.models import Manufacturer
from shuup.testing.factories import get_default_shop, create_product, get_random_filer_image


def setup_function(fn):
    cache.clear()


def test_manufacturer_api(admin_user):
    get_default_shop()
    client = APIClient()
    client.force_authenticate(user=admin_user)
    image = get_random_filer_image()
    with open(image.path, 'rb') as f:
        img_base64 = base64.b64encode(os.urandom(50)).decode()
        uri = "data:application/octet-stream;base64,{}".format(img_base64)
    manufacturer_data = {
        "name": "manu 1",
        "url": "http://www.google.com",
        "logo_path" : "/this/not/needed",
        "logo" : uri
    }
    response = client.post("/api/shuup/manufacturer/",
                           content_type="application/json",
                           data=json.dumps(manufacturer_data))
    assert response.status_code == status.HTTP_201_CREATED
    manufacturer = Manufacturer.objects.first()
    assert manufacturer.name == manufacturer_data["name"]
    assert manufacturer.url == manufacturer_data["url"]
    assert manufacturer.logo.folder.pretty_logical_path == manufacturer_data["logo_path"]
    with open(manufacturer.logo.path, 'rb') as f:
        assert img_base64 == base64.b64encode(f.read()).decode()

    manufacturer_data.pop("logo_path") # Test error when not sending a path


    response = client.post("/api/shuup/manufacturer/",
                           content_type="application/json",
                           data=json.dumps(manufacturer_data))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = json.loads(response.content.decode("utf-8"))
    assert data["non_field_errors"][0] == "Path is required when sending a manufacturer logo."

    manufacturer_data["logo_path"] = "/second/path" # Testing second manufacturer
    manufacturer_data["name"] = "name 2"
    manufacturer_data["url"] = "http://yahoo.com"

    response = client.put("/api/shuup/manufacturer/%d/" % manufacturer.id,
                          content_type="application/json",
                          data=json.dumps(manufacturer_data))
    assert response.status_code == status.HTTP_200_OK
    manufacturer = Manufacturer.objects.first()
    assert manufacturer.name == manufacturer_data["name"]
    assert manufacturer.url == manufacturer_data["url"]
    response = client.get("/api/shuup/manufacturer/%d/" % manufacturer.id)
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert manufacturer.name == data["name"]
    assert manufacturer.url == data["url"]

    response = client.get("/api/shuup/manufacturer/")
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert manufacturer.name == data[0]["name"]
    assert manufacturer.url == data[0]["url"]

    response = client.delete("/api/shuup/manufacturer/%d/" % manufacturer.id)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Manufacturer.objects.count() == 0

    # create a product and relate it to a manufacturer
    product = create_product("product with manufacturer")
    manufacturer = Manufacturer.objects.create()
    product.manufacturer = manufacturer
    product.save()

    # shouldn't be possible to delete a manufacturer with a related product
    response = client.delete("/api/shuup/manufacturer/%d/" % manufacturer.id)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "This object can not be deleted because it is referenced by" in response.content.decode("utf-8")
    assert Manufacturer.objects.count() == 1
