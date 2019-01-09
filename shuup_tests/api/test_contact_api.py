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
from shuup.core.models import Contact, Gender, PersonContact
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


def test_person_contact_api(admin_user):
    shop = get_default_shop()
    client = _get_client(admin_user)
    PersonContact.objects.all().delete()

    contact_data = {
        "name": "Person Contact Name",
        "gender": Gender.FEMALE.value,
        "phone": "312312312",
        "email": "goodemail@apitest.com.cz"
    }
    response = client.post("/api/shuup/person_contact/",
                           content_type="application/json",
                           data=json.dumps(contact_data))
    assert response.status_code == status.HTTP_201_CREATED
    person_contact = PersonContact.objects.first()
    assert person_contact.name == contact_data["name"]
    assert person_contact.gender.value == contact_data["gender"]
    assert person_contact.phone == contact_data["phone"]
    assert person_contact.email == contact_data["email"]

    contact_data["name"] = "Changed Name"
    contact_data["gender"] = Gender.MALE.value
    contact_data["phone"] = "391891892"
    contact_data["email"] = "ihavechanged@email.comz"

    response = client.put("/api/shuup/person_contact/%d/" % person_contact.id,
                          content_type="application/json",
                          data=json.dumps(contact_data))
    assert response.status_code == status.HTTP_200_OK
    person_contact = PersonContact.objects.first()
    assert person_contact.name == contact_data["name"]
    assert person_contact.gender.value == contact_data["gender"]
    assert person_contact.phone == contact_data["phone"]
    assert person_contact.email == contact_data["email"]

    response = client.get("/api/shuup/person_contact/%d/" % person_contact.id)
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert person_contact.name == data["name"]
    assert person_contact.gender.value == data["gender"]
    assert person_contact.phone == data["phone"]
    assert person_contact.email == data["email"]

    # change some data
    contact_data = {"name": "Changed again"}
    response = client.patch("/api/shuup/person_contact/%d/" % person_contact.id,
                            content_type="application/json",
                            data=json.dumps(contact_data))
    assert response.status_code == status.HTTP_200_OK
    person_contact = PersonContact.objects.first()
    assert person_contact.name == contact_data["name"]

    response = client.delete("/api/shuup/person_contact/%d/" % person_contact.id)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert PersonContact.objects.count() == 0


def _get_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client
