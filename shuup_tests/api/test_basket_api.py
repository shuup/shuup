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
from shuup.core.models import (
    get_person_contact, Order, OrderStatus, PaymentStatus, ShippingStatus,
    Shop, ShopStatus, Basket
)
from shuup.core.pricing import TaxfulPrice
from shuup.testing import factories
from shuup_tests.campaigns.test_discount_codes import (
    Coupon, get_default_campaign
)


def setup_function(fn):
    cache.clear()

def configure(settings):
    settings.SHUUP_ENABLE_MULTIPLE_SHOPS = True
    SHUUP_BASKET_ORDER_CREATOR_SPEC = (
        "shuup.core.basket.order_creator:BasketOrderCreator")
    settings.SHUUP_BASKET_STORAGE_CLASS_SPEC = (
        "shuup.core.basket.storage:DatabaseBasketStorage")
    settings.SHUUP_BASKET_CLASS_SPEC = (
        "shuup.core.basket.objects:Basket")
    settings.MIDDLEWARE_CLASSES = [
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.middleware.locale.LocaleMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware'
    ]

def create_shop(name):
    return Shop.objects.create(
        name="foobar",
        identifier=name,
        status=ShopStatus.ENABLED,
        public_name=name,
        currency=factories.get_default_currency().code
    )

@pytest.mark.django_db
def test_create_new_basket(admin_user, settings):
    configure(settings)
    shop = factories.get_default_shop()
    shop2 = create_shop("foobar")
    client = _get_client(admin_user)
    response = client.post("/api/shuup/basket/new/", {
        "shop": shop2.pk
    })
    assert response.status_code == status.HTTP_201_CREATED
    basket_data = json.loads(response.content.decode("utf-8"))
    basket = Basket.objects.first()
    assert basket.key == basket_data['uuid'].split("-")[1]
    assert basket.shop == shop2
    assert basket.creator == admin_user

    # invalid shop
    response = client.post("/api/shuup/basket/new/", {
        "shop": 1000
    })
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # no shop in multishop mode
    response = client.post("/api/shuup/basket/new/")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # no shop in single shop mode
    settings.SHUUP_ENABLE_MULTIPLE_SHOPS = False
    response = client.post("/api/shuup/basket/new/")
    assert response.status_code == status.HTTP_201_CREATED
    basket_data = json.loads(response.content.decode("utf-8"))
    basket = Basket.objects.all()[1]
    assert basket.key == basket_data['uuid'].split("-")[1]
    assert basket.shop == shop
    assert basket.creator == admin_user


@pytest.mark.django_db
def test_fetch_basket(admin_user, settings):
    configure(settings)
    shop = factories.get_default_shop()
    shop2 = create_shop("foobar")
    basket = factories.get_basket()
    factories.get_default_payment_method()
    factories.get_default_shipping_method()
    assert basket.shop == shop
    client = _get_client(admin_user)
    response = client.get('/api/shuup/basket/{}-{}/'.format(shop.pk, basket.key))
    assert response.status_code == status.HTTP_200_OK
    basket_data = json.loads(response.content.decode("utf-8"))
    assert basket_data["key"] == basket.key
    assert not basket_data["validation_errors"]
    # malformed uuid
    response = client.get('/api/shuup/basket/{}/'.format(basket.key))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    # wrong shop
    response = client.get('/api/shuup/basket/{}-{}/'.format(shop2.pk, basket.key))
    assert response.status_code == 400


@pytest.mark.django_db
def test_add_product_to_basket(admin_user, settings):
    configure(settings)
    shop = factories.get_default_shop()
    basket = factories.get_basket()
    factories.get_default_payment_method()
    factories.get_default_shipping_method()
    shop_product = factories.get_default_shop_product()
    shop_product.default_price = TaxfulPrice(1, shop.currency)
    shop_product.save()
    client = _get_client(admin_user)
    # add shop product
    payload = {
        'shop_product': shop_product.id
    }
    response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.pk, basket.key), payload)
    assert response.status_code == status.HTTP_200_OK

    response_data = json.loads(response.content.decode("utf-8"))
    assert len(response_data["items"]) == 1
    assert response_data["items"][0]["shop_product"] == shop_product.pk
    assert not response_data["validation_errors"]
    assert float(response_data["total_price"]) == 1

    # add product
    payload = {
        'product': shop_product.product.pk,
        'shop': shop.pk
    }
    response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.pk, basket.key), payload)
    assert response.status_code == status.HTTP_200_OK
    response_data = json.loads(response.content.decode("utf-8"))
    assert len(response_data["items"]) == 1
    assert not response_data["validation_errors"]
    assert float(response_data["total_price"]) == 2


@pytest.mark.django_db
def test_add_product_shop_mismatch(admin_user, settings):
    configure(settings)
    shop = factories.get_default_shop()
    shop2 = create_shop("foobar")
    basket = factories.get_basket()
    factories.get_default_payment_method()
    factories.get_default_shipping_method()
    sp = factories.create_product("test", shop=shop2, supplier=factories.get_default_supplier()).get_shop_instance(shop2)
    client = _get_client(admin_user)
    payload = {
        'shop_product': sp.id
    }
    response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.pk, basket.key), payload)
    assert response.status_code == 400
    assert "different shop" in str(response.content)

    # add product belonging to different shop than basket shop
    payload = {
        'shop': sp.shop.id,
        'product': sp.product.id
    }
    response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.pk, basket.key), payload)
    assert response.status_code == 400
    assert "different shop" in str(response.content)


@pytest.mark.django_db
def test_product_is_required_when_adding(admin_user, settings):
    configure(settings)
    shop = factories.get_default_shop()
    basket = factories.get_basket()
    shop_product = factories.get_default_shop_product()
    client = _get_client(admin_user)
    payload = {
        'shop': shop.id,
    }
    response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.id, basket.key), payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert '"product"' in str(response.content)


@pytest.mark.django_db
def test_quantity_has_to_be_in_stock(admin_user, settings):
    configure(settings)
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
    response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.pk, basket.key), payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert '"Insufficient stock"' in str(response.content)


@pytest.mark.django_db
def test_product_has_to_exist(admin_user, settings):
    configure(settings)
    shop = factories.get_default_shop()
    basket = factories.get_basket()
    client = _get_client(admin_user)
    # invalid product
    payload = {
        'shop': shop.id,
        'product': 2384958,
    }
    response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.pk, basket.key), payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "object does not exist" in str(response.content)

    # invalid shop product
    payload = {
        'shop_product': 2384958
    }
    response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.pk, basket.key), payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "object does not exist" in str(response.content)


@pytest.mark.django_db
def test_update_line_quantity(admin_user, settings):
    configure(settings)
    shop = factories.get_default_shop()
    basket = factories.get_basket()
    factories.get_default_payment_method()
    factories.get_default_shipping_method()
    shop_product = factories.get_default_shop_product()
    shop_product.default_price = TaxfulPrice(1, shop.currency)
    shop_product.save()
    client = _get_client(admin_user)
    # add shop product
    payload = {
        'shop_product': shop_product.id
    }
    response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.pk, basket.key), payload)
    assert response.status_code == status.HTTP_200_OK

    response_data = json.loads(response.content.decode("utf-8"))
    assert len(response_data["items"]) == 1

    payload = {
        "line_id": response_data["items"][0]["line_id"],
        "quantity": 5
    }
    response = client.post('/api/shuup/basket/{}-{}/update_quantity/'.format(shop.pk, basket.key), payload)
    assert response.status_code == status.HTTP_200_OK

    response_data = json.loads(response.content.decode("utf-8"))
    assert len(response_data["items"]) == 1
    assert response_data["items"][0]["shop_product"] == shop_product.pk
    assert float(response_data["items"][0]["quantity"]) == 5
    assert float(response_data["total_price"]) == 5
    basket.refresh_from_db()
    assert Basket.objects.first().data["lines"][0]["quantity"] == 5


@pytest.mark.django_db
def test_basket_can_be_cleared(admin_user, settings):
    configure(settings)
    shop = factories.get_default_shop()
    basket = factories.get_basket()
    shop_product = factories.get_default_shop_product()
    client = _get_client(admin_user)
    payload = {
        'shop': shop.id,
        'product': shop_product.id,
    }
    response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.id, basket.key), payload)
    assert response.status_code == status.HTTP_200_OK
    basket = Basket.objects.get(key=basket.key)
    assert basket.product_count == 1

    response = client.post('/api/shuup/basket/{}-{}/clear/'.format(shop.id, basket.key), payload)
    response_data = json.loads(response.content.decode("utf-8"))
    assert response.status_code == status.HTTP_200_OK
    basket.refresh_from_db()
    assert basket.product_count == 0
    assert len(response_data["items"]) == 0

@pytest.mark.django_db
def test_can_delete_line(admin_user, settings):
    configure(settings)
    shop = factories.get_default_shop()
    basket = factories.get_basket()
    shop_product = factories.get_default_shop_product()
    client = _get_client(admin_user)
    payload = {
        'shop_product': shop_product.id,
    }
    response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.id, basket.key), payload)
    assert response.status_code == status.HTTP_200_OK
    response_data = json.loads(response.content.decode("utf-8"))
    basket.refresh_from_db()
    assert len(response_data["items"]) == 1
    assert basket.product_count == 1
    line_id = response_data["items"][0]["line_id"]
    payload = {
        'line_id': line_id
    }
    response = client.post('/api/shuup/basket/{}-{}/remove/'.format(shop.id, basket.key), payload)
    response_data = json.loads(response.content.decode("utf-8"))
    assert response.status_code == status.HTTP_200_OK
    basket.refresh_from_db()
    assert basket.product_count == 0
    assert len(response_data["items"]) == 0


@pytest.mark.django_db
def test_add_blank_code(admin_user, settings):
    configure(settings)
    configure(settings)
    shop = factories.get_default_shop()
    basket = factories.get_basket()
    shop_product = factories.get_default_shop_product()
    client = _get_client(admin_user)
    payload = {
        'code': ''
    }
    response = client.post('/api/shuup/basket/{}-{}/add_code/'.format(shop.pk, basket.key), payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_data = json.loads(response.content.decode("utf-8"))
    assert 'code' in response_data


@pytest.mark.django_db
def test_cant_add_a_dummy_campaign_code(admin_user, settings):
    configure(settings)
    shop = factories.get_default_shop()
    basket = factories.get_basket()
    shop_product = factories.get_default_shop_product()
    client = _get_client(admin_user)
    payload = {
        'code': 'ABCDE'
    }
    response = client.post('/api/shuup/basket/{}-{}/add_code/'.format(shop.pk, basket.key), payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_can_add_a_valid_campaign_code(admin_user, settings):
    configure(settings)
    shop = factories.get_default_shop()
    basket = factories.get_basket()
    shop_product = factories.get_default_shop_product()
    client = _get_client(admin_user)

    coupon = Coupon.objects.create(code="DACODE", active=True)
    get_default_campaign(coupon)

    payload = {
        'code': 'DACODE'
    }
    response = client.post('/api/shuup/basket/{}-{}/add_code/'.format(shop.pk, basket.key), payload)
    basket_data = json.loads(response.content.decode("utf-8"))
    assert response.status_code == status.HTTP_200_OK
    assert 'DACODE' in basket_data['codes']


@pytest.mark.django_db
def test_create_order(admin_user, settings):
    configure(settings)
    shop = factories.get_default_shop()
    basket = factories.get_basket()
    factories.create_default_order_statuses()
    shop_product = factories.get_default_shop_product()
    shop_product.default_price = TaxfulPrice(1, shop.currency)
    shop_product.save()
    client = _get_client(admin_user)
    # add shop product
    payload = {
        'shop_product': shop_product.id
    }
    response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.pk, basket.key), payload)
    assert response.status_code == status.HTTP_200_OK

    response_data = json.loads(response.content.decode("utf-8"))
    assert len(response_data["items"]) == 1
    response = client.post('/api/shuup/basket/{}-{}/create_order/'.format(shop.pk, basket.key), payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_data = json.loads(response.content.decode("utf-8"))
    assert "errors" in response_data

    factories.get_default_payment_method()
    factories.get_default_shipping_method()
    response = client.post('/api/shuup/basket/{}-{}/create_order/'.format(shop.pk, basket.key), payload)
    assert response.status_code == status.HTTP_201_CREATED
    response_data = json.loads(response.content.decode("utf-8"))
    basket.refresh_from_db()
    assert basket.finished
    order = Order.objects.get(reference_number=response_data["reference_number"])
    assert order.status == OrderStatus.objects.get_default_initial()
    assert order.payment_status == PaymentStatus.NOT_PAID
    assert order.shipping_status == ShippingStatus.NOT_SHIPPED
    assert not order.payment_method
    assert not order.shipping_method
    assert float(order.taxful_total_price_value) == 1
    assert order.customer == get_person_contact(admin_user)
    assert order.orderer == get_person_contact(admin_user)
    assert order.creator == admin_user
    assert not order.billing_address
    assert not order.shipping_address


def _get_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client
