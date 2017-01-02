# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json

from rest_framework import status
from rest_framework.test import APIClient

from shuup.core import cache
from shuup.core.models import Contact
from shuup.testing.factories import (
    create_random_person, get_default_customer_group, get_default_shop
)


def setup_function(fn):
    cache.clear()


def test_get_by_pk(admin_user):
    get_default_shop()
    for i in range(0,10):
        create_random_person()

    contact = create_random_person()
    client = _get_client(admin_user)
    response = client.get("/api/shuup/contact/%s/" % contact.id)
    assert response.status_code == status.HTTP_200_OK
    contact_data = json.loads(response.content.decode("utf-8"))
    assert contact_data.get("id") == contact.id
    assert contact_data.get("name") == contact.name


def test_get_by_email(admin_user):
    get_default_shop()
    for i in range(0, 10):
        create_random_person()

    contact = create_random_person()
    client = _get_client(admin_user)

    response = client.get("/api/shuup/contact/", data={"email": contact.email})
    assert response.status_code == status.HTTP_200_OK
    contact_data = json.loads(response.content.decode("utf-8"))

    assert Contact.objects.filter(email=contact.email).count() == len(contact_data)
    assert contact_data[0].get("id") == contact.id
    assert contact_data[0].get("email") == contact.email
    assert contact_data[0].get("name") == contact.name


def test_get_by_contact_group(admin_user):
    get_default_shop()
    for i in range(0, 10):
        create_random_person()

    contact = create_random_person()
    group = get_default_customer_group()
    group.members.add(contact)

    client = _get_client(admin_user)

    response = client.get("/api/shuup/contact/", data={"groups": group.id})
    assert response.status_code == status.HTTP_200_OK
    contact_data = json.loads(response.content.decode("utf-8"))

    assert group.members.count() == len(contact_data)
    assert contact_data[0].get("id") == contact.id
    assert contact_data[0].get("email") == contact.email
    assert contact_data[0].get("name") == contact.name


def _get_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client
