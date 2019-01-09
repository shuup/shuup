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
from shuup.core.models import TaxClass
from shuup.testing.factories import get_default_shop, create_product


def setup_function(fn):
    cache.clear()


def test_tax_class_api(admin_user):
    get_default_shop()
    client = APIClient()
    client.force_authenticate(user=admin_user)

    tax_class_data = {
        "translations": {
            "en": {"name": "tax class 1"}
        },
        "enabled": True
    }
    response = client.post("/api/shuup/tax_class/",
                           content_type="application/json",
                           data=json.dumps(tax_class_data))
    assert response.status_code == status.HTTP_201_CREATED
    tax_class = TaxClass.objects.first()
    assert tax_class.name == tax_class_data["translations"]["en"]["name"]
    assert tax_class.enabled == tax_class_data["enabled"]

    tax_class_data["translations"]["en"]["name"] = "Tax class 2"
    tax_class_data["enabled"] = False

    response = client.put("/api/shuup/tax_class/%d/" % tax_class.id,
                          content_type="application/json",
                          data=json.dumps(tax_class_data))
    assert response.status_code == status.HTTP_200_OK
    tax_class = TaxClass.objects.first()
    assert tax_class.name == tax_class_data["translations"]["en"]["name"]
    assert tax_class.enabled == tax_class_data["enabled"]

    response = client.get("/api/shuup/tax_class/%d/" % tax_class.id)
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert tax_class.name == data["translations"]["en"]["name"]
    assert tax_class.enabled == tax_class_data["enabled"]

    response = client.get("/api/shuup/tax_class/")
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert tax_class.name == data[0]["translations"]["en"]["name"]
    assert tax_class.enabled == data[0]["enabled"]

    response = client.delete("/api/shuup/tax_class/%d/" % tax_class.id)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert TaxClass.objects.count() == 0

    tax_class = TaxClass.objects.create(name="class1")
    product = create_product("product1", tax_class=tax_class)
    # shouldn't be possible to delete a tax_class with a related product
    response = client.delete("/api/shuup/tax_class/%d/" % tax_class.id)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "This object can not be deleted because it is referenced by" in response.content.decode("utf-8")
