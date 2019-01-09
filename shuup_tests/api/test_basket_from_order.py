# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json

import pytest
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient

from shuup.core.models import AnonymousContact, get_person_contact
from shuup.testing import factories

from shuup.testing.basket_helpers import (
    get_client, REQUIRED_SETTINGS, set_configuration
)


@pytest.mark.django_db
def test_copy_order_to_basket(admin_user):
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        shop = factories.get_default_shop()
        order = _create_order(shop, get_person_contact(admin_user))

        client = get_client(admin_user)
        basket = factories.get_basket(shop)
        # No need to assign basket customer separately since the
        # API will use request customer as default customer

        _fill_new_basket_from_order(client, basket, order.customer, order)

        # do it again, basket should clear first then read items
        _fill_new_basket_from_order(client, basket, order.customer, order)


@pytest.mark.django_db
def test_copy_order_to_basket_for_anonymous():
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        shop = factories.get_default_shop()
        order = _create_order(shop, AnonymousContact())

        basket = factories.get_basket(shop)
        assert basket.customer is None
        client = APIClient()

        assert basket.customer is None
        _fill_new_basket_from_order(client, basket, None, order)

        # do it again, basket should clear first then read items
        _fill_new_basket_from_order(client, basket, None, order)


@pytest.mark.django_db
def test_copy_order_to_basket_for_staff(admin_user):
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        shop = factories.get_default_shop()
        customer = factories.create_random_person()
        order = _create_order(shop, customer)

        client = get_client(admin_user)
        basket = factories.get_basket(shop)
        uuid = "%s-%s" % (shop.pk, basket.key)
        response = client.post(
            '/api/shuup/basket/%s/set_customer/' % uuid, format="json", data={"customer": customer.id}
        )
        assert response.status_code == status.HTTP_200_OK

        response = client.post('/api/shuup/basket/%s/add_from_order/' % uuid, {"order": order.pk})
        assert response.status_code == status.HTTP_404_NOT_FOUND  # admin user is not staff

        shop.staff_members.add(admin_user)
        _fill_new_basket_from_order(client, basket, customer, order)


def _create_order(shop, customer):
    p1 = factories.create_product("test", shop=shop, supplier=factories.get_default_supplier())
    order = factories.create_order_with_product(factories.get_default_product(), factories.get_default_supplier(), 2,
                                                10, shop=shop)
    factories.add_product_to_order(order, factories.get_default_supplier(), p1, 2, 5)
    order.customer = customer
    order.save()
    return order


def _fill_new_basket_from_order(client, basket, basket_customer, order):
    uuid = "%s-%s" % (order.shop.pk, basket.key)
    response = client.post('/api/shuup/basket/%s/add_from_order/' % uuid, {"order": order.pk})
    assert response.status_code == status.HTTP_200_OK
    response_data = json.loads(response.content.decode("utf-8"))
    assert len(response_data["items"]) == 2
    assert not response_data["validation_errors"]
    basket.refresh_from_db()
    assert len(basket.data["lines"]) == 2
    assert basket.customer == basket_customer
