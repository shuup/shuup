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
    price_display_option = group.price_display_options.first()
    client = APIClient()
    client.force_authenticate(user=admin_user)
    response = client.get("/api/shuup/contact_group_price_display/%s/" % price_display_option.pk)
    assert response.status_code == status.HTTP_200_OK

    price_display_data = json.loads(response.content.decode("utf-8"))
    assert price_display_data["group"] == group.id


def test_patch(admin_user):
    activate("en")
    shop = get_default_shop()
    group = get_default_customer_group()
    price_display_option = group.price_display_options.first()
    client = APIClient()
    client.force_authenticate(user=admin_user)
    assert price_display_option.show_pricing
    data = {"show_pricing": False}
    response = client.patch(
        path="/api/shuup/contact_group_price_display/%s/" % price_display_option.pk,
        data=data
    )
    assert response.status_code == status.HTTP_200_OK

    contact_group_data = json.loads(response.content.decode("utf-8"))
    group_id = contact_group_data["id"]
    assert not contact_group_data["show_pricing"]
