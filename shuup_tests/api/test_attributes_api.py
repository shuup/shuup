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
from shuup.core.models import Attribute, AttributeType, AttributeVisibility
from shuup.testing.factories import get_default_shop


def setup_function(fn):
    cache.clear()


def test_attr_api(admin_user):
    activate("en")
    get_default_shop()
    client = APIClient()
    client.force_authenticate(user=admin_user)

    attr_data = {
        "identifier": "attr1",
        "translations": {
            "en": {"name": "Kilo"}
        },
        "searchable": False,
        "type": AttributeType.BOOLEAN.value,
        "visibility_mode": AttributeVisibility.HIDDEN.value
    }
    response = client.post("/api/shuup/attribute/",
                           content_type="application/json",
                           data=json.dumps(attr_data))
    assert response.status_code == status.HTTP_201_CREATED
    attr = Attribute.objects.first()
    assert attr.name == attr_data["translations"]["en"]["name"]
    assert attr.searchable == attr_data["searchable"]
    assert attr.type.value == attr_data["type"]
    assert attr.identifier == attr_data["identifier"]
    assert attr.visibility_mode.value == attr_data["visibility_mode"]

    attr_data["translations"]["en"]["name"] = "Pound"
    attr_data["identifier"] = "attr2"
    attr_data["searchable"] = True
    attr_data["type"] = AttributeType.DECIMAL.value
    attr_data["visibility_mode"] = AttributeVisibility.SEARCHABLE_FIELD.value

    response = client.put("/api/shuup/attribute/%d/" % attr.id,
                          content_type="application/json",
                          data=json.dumps(attr_data))
    assert response.status_code == status.HTTP_200_OK
    attr = Attribute.objects.first()
    assert attr.name == attr_data["translations"]["en"]["name"]
    assert attr.searchable == attr_data["searchable"]
    assert attr.type.value == attr_data["type"]
    assert attr.identifier == attr_data["identifier"]
    assert attr.visibility_mode.value == attr_data["visibility_mode"]

    response = client.get("/api/shuup/attribute/%d/" % attr.id)
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert attr.name == data["translations"]["en"]["name"]
    assert attr.searchable == attr_data["searchable"]
    assert attr.type.value == attr_data["type"]
    assert attr.identifier == attr_data["identifier"]
    assert attr.visibility_mode.value == attr_data["visibility_mode"]

    response = client.get("/api/shuup/attribute/")
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert attr.searchable == data[0]["searchable"]
    assert attr.type.value == data[0]["type"]
    assert attr.identifier == data[0]["identifier"]
    assert attr.visibility_mode.value == data[0]["visibility_mode"]

    response = client.delete("/api/shuup/attribute/%d/" % attr.id)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Attribute.objects.count() == 0
