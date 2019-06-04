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
from shuup.core.models import Contact, ContactGroup, Gender, PersonContact
from shuup.testing.factories import (
    get_default_customer_group, get_default_shop
)


def test_fetch(admin_user):
    activate("en")
    get_default_shop()
    group = get_default_customer_group()
    client = APIClient()
    client.force_authenticate(user=admin_user)
    response = client.get("/api/shuup/contact_group/%s/" % group.pk)
    assert response.status_code == status.HTTP_200_OK

    contact_group_data = json.loads(response.content.decode("utf-8"))
    assert contact_group_data["id"] == group.id
    assert contact_group_data["translations"]["en"]["name"] == group.name


def test_create(admin_user):
    activate("en")
    shop = get_default_shop()
    client = APIClient()
    client.force_authenticate(user=admin_user)
    group_name = "hello world"
    data = {
        "shop": shop.pk,
        "translations": {"en": {"name": group_name}}
    }
    response = client.post(
        path="/api/shuup/contact_group/",
        content_type="application/json",
        data=json.dumps(data))
    assert response.status_code == status.HTTP_201_CREATED

    contact_group_data = json.loads(response.content.decode("utf-8"))
    group_id = contact_group_data["id"]
    assert contact_group_data["translations"]["en"]["name"] == group_name
    assert ContactGroup.objects.filter(id=group_id).first().name == group_name
