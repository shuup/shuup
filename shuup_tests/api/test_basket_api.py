# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
import json

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from shuup.core import cache
from shuup.front.models import StoredBasket
from shuup_tests.campaigns.test_discount_codes import get_default_campaign, Coupon
from shuup.testing import factories


def setup_function(fn):
    cache.clear()


@pytest.mark.django_db
def test_create_new_basket(admin_user):
    shop = factories.get_default_shop()
    client = _get_client(admin_user)
    response = client.post("/api/shuup/basket/new/")
    assert response.status_code == status.HTTP_201_CREATED
    basket_data = json.loads(response.content.decode("utf-8"))
    assert len(basket_data.get("uuid")) == 32
    basket = StoredBasket.objects.first()
    assert basket.key == basket_data['uuid']


@pytest.mark.django_db
def test_fetch_basket(admin_user):
    shop = factories.get_default_shop()
    basket = factories.get_basket()
    assert basket.shop == shop
    client = _get_client(admin_user)
    response = client.get('/api/shuup/basket/{}/'.format(basket.key))
    assert response.status_code == status.HTTP_200_OK
    basket_data = json.loads(response.content.decode("utf-8"))
    assert basket_data["key"] == basket.key


@pytest.mark.django_db
def test_add_product_to_basket(admin_user):
    shop = factories.get_default_shop()
    basket = factories.get_basket()
    shop_product = factories.get_default_shop_product()
    client = _get_client(admin_user)
    payload = {
        'shop': shop.id,
        'product': shop_product.id,
    }
    response = client.post('/api/shuup/basket/{}/add/'.format(basket.key), payload)
    assert response.status_code == status.HTTP_200_OK

    response_data = json.loads(response.content.decode("utf-8"))
    assert 'line_id' in response_data
    assert 'product_count' in response_data
    assert response_data['added'] == 1


@pytest.mark.django_db
def test_product_is_required_when_adding(admin_user):
    shop = factories.get_default_shop()
    basket = factories.get_basket()
    shop_product = factories.get_default_shop_product()
    client = _get_client(admin_user)
    payload = {
        'shop': shop.id,
    }
    response = client.post('/api/shuup/basket/{}/add/'.format(basket.key), payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert '"product"' in str(response.content)


@pytest.mark.django_db
def test_quantity_as_to_be_in_stock(admin_user):
    from shuup_tests.simple_supplier.utils import get_simple_supplier
    from shuup.core.models import StockBehavior
    shop = factories.get_default_shop()
    basket = factories.get_basket()

    supplier = get_simple_supplier()
    product = factories.create_product("simple-test-product", shop, supplier)
    quantity = 256
    supplier.adjust_stock(product.pk, quantity)
    product.stock_behavior = StockBehavior.STOCKED
    product.save()
    shop_product = product.shop_products.first()
    shop_product.suppliers.add(supplier)
    shop_product.save()

    client = _get_client(admin_user)
    payload = {
        'shop': shop.id,
        'product': shop_product.id,
        'quantity': 493020
    }
    response = client.post('/api/shuup/basket/{}/add/'.format(basket.key), payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert '"Insufficient stock"' in str(response.content)


@pytest.mark.django_db
def test_product_has_to_exist(admin_user):
    shop = factories.get_default_shop()
    basket = factories.get_basket()
    shop_product = factories.get_default_shop_product()
    client = _get_client(admin_user)
    payload = {
        'shop': shop.id,
        'product': 2384958,
    }
    response = client.post('/api/shuup/basket/{}/add/'.format(basket.key), payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert '"product_not_available_in_shop"' in str(response.content)


@pytest.mark.django_db
def test_basket_can_be_cleared(admin_user):
    shop = factories.get_default_shop()
    basket = factories.get_basket()
    shop_product = factories.get_default_shop_product()
    client = _get_client(admin_user)
    payload = {
        'shop': shop.id,
        'product': shop_product.id,
    }
    response = client.post('/api/shuup/basket/{}/add/'.format(basket.key), payload)
    assert response.status_code == status.HTTP_200_OK
    basket = StoredBasket.objects.get(key=basket.key)
    assert basket.product_count == 1

    response = client.post('/api/shuup/basket/{}/clear/'.format(basket.key), payload)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    basket = StoredBasket.objects.get(key=basket.key)
    assert basket.product_count == 0


@pytest.mark.django_db
def test_can_delete_line(admin_user):
    shop = factories.get_default_shop()
    basket = factories.get_basket()
    shop_product = factories.get_default_shop_product()
    client = _get_client(admin_user)
    payload = {
        'shop': shop.id,
        'product': shop_product.id,
    }
    response = client.post('/api/shuup/basket/{}/add/'.format(basket.key), payload)
    assert response.status_code == status.HTTP_200_OK
    response_data = json.loads(response.content.decode("utf-8"))
    line_id = response_data['line_id']
    assert line_id is not None

    payload = {
        'line_id': line_id
    }
    response = client.post('/api/shuup/basket/{}/remove/'.format(basket.key), payload)
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_cant_add_a_dummy_campaign_code(admin_user):
    shop = factories.get_default_shop()
    basket = factories.get_basket()
    shop_product = factories.get_default_shop_product()
    client = _get_client(admin_user)
    payload = {
        'code': 'ABCDE'
    }
    response = client.post('/api/shuup/basket/{}/add_code/'.format(basket.key), payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_can_add_a_valid_campaign_code(admin_user):
    shop = factories.get_default_shop()
    basket = factories.get_basket()
    shop_product = factories.get_default_shop_product()
    client = _get_client(admin_user)

    coupon = Coupon.objects.create(code="DACODE", active=True)
    get_default_campaign(coupon)

    payload = {
        'code': 'DACODE'
    }
    response = client.post('/api/shuup/basket/{}/add_code/'.format(basket.key), payload)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = client.get('/api/shuup/basket/{}/'.format(basket.key))
    assert response.status_code == status.HTTP_200_OK
    basket_data = json.loads(response.content.decode("utf-8"))
    assert basket_data['codes'] == ['DACODE']


def _get_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client
