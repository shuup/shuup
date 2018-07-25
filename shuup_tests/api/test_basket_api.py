# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json
from datetime import timedelta
from decimal import Decimal

import babel
import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.test import override_settings
from django.utils.timezone import now
from pytest_django.fixtures import django_user_model, django_username_field
from rest_framework import status
from rest_framework.test import APIClient

from shuup.core import cache
from shuup.core.models import (
    Basket, Currency, get_person_contact, Order, OrderLineType,
    OrderStatusManager, Product, ProductMedia, ProductMediaKind, Shop,
    ShopProduct, ShopProductVisibility, ShopStatus
)
from shuup.core.pricing import TaxfulPrice
from shuup.testing import factories
from shuup.testing.factories import (
    create_default_tax_rule, create_product, get_default_currency,
    get_default_supplier, get_default_tax, get_random_filer_image, get_tax
)
from shuup.utils.i18n import get_current_babel_locale
from shuup_tests.campaigns.test_discount_codes import (
    Coupon, get_default_campaign
)

from shuup.testing.basket_helpers import (
    get_client, REQUIRED_SETTINGS, set_configuration
)


def setup_function(fn):
    cache.clear()


def create_shop(name):
    return Shop.objects.create(
        name="foobar",
        identifier=name,
        status=ShopStatus.ENABLED,
        public_name=name,
        currency=factories.get_default_currency().code
    )

@pytest.mark.django_db
def test_create_new_basket(admin_user):
    with override_settings(**REQUIRED_SETTINGS):
        shop = factories.get_default_shop()
        shop2 = create_shop("foobar")
        client = get_client(admin_user)
        response = client.post("/api/shuup/basket/new/", {
            "shop": shop2.pk
        })
        assert response.status_code == status.HTTP_201_CREATED
        basket_data = json.loads(response.content.decode("utf-8"))
        basket = Basket.objects.first()
        assert basket.key == basket_data['uuid'].split("-")[1]
        assert basket.shop == shop2
        admin_contact = get_person_contact(admin_user)
        assert basket.customer == admin_contact
        assert basket.orderer == admin_contact
        assert basket.creator == admin_user

        # invalid shop
        response = client.post("/api/shuup/basket/new/", {"shop": 1000})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # no shop in multishop mode
        response = client.post("/api/shuup/basket/new/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # no shop in single shop mode
        with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=False):
            response = client.post("/api/shuup/basket/new/")
            assert response.status_code == status.HTTP_201_CREATED
            basket_data = json.loads(response.content.decode("utf-8"))
            basket = Basket.objects.all()[1]
            assert basket.key == basket_data['uuid'].split("-")[1]
            assert basket.shop == shop
            assert basket.customer == admin_contact
            assert basket.orderer == admin_contact
            assert basket.creator == admin_user


@pytest.mark.django_db
def test_fetch_basket(admin_user):
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        shop = factories.get_default_shop()
        shop2 = create_shop("foobar")
        basket = factories.get_basket()
        factories.get_default_payment_method()
        factories.get_default_shipping_method()
        assert basket.shop == shop
        client = get_client(admin_user)
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
        assert response.status_code == 404


@pytest.mark.django_db
def test_add_product_to_basket(admin_user):
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        shop = factories.get_default_shop()
        basket = factories.get_basket()
        factories.get_default_payment_method()
        factories.get_default_shipping_method()
        shop_product = factories.get_default_shop_product()
        product_price = 1
        shop_product.default_price = TaxfulPrice(product_price, shop.currency)
        shop_product.save()
        client = get_client(admin_user)
        # add shop product
        payload = {
            'shop_product': shop_product.id
        }
        response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.pk, basket.key), payload)
        assert response.status_code == status.HTTP_200_OK

        response_data = json.loads(response.content.decode("utf-8"))
        assert response_data["add_line_id"]
        assert len(response_data["items"]) == 1
        assert response_data["items"][0]["shop_product"] == shop_product.pk
        assert not response_data["validation_errors"]
        assert float(response_data["total_price"]) == 1 * product_price

        # add product
        payload = {
            'product': shop_product.product.pk,
            'shop': shop.pk
        }
        precision = Decimal("0.01")
        response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.pk, basket.key), payload)
        assert response.status_code == status.HTTP_200_OK
        response_data = json.loads(response.content.decode("utf-8"))
        assert len(response_data["items"]) == 1
        assert not response_data["validation_errors"]

        expected_price = Decimal(2 * product_price).quantize(precision)
        assert Decimal(response_data["total_price"]) == expected_price
        assert Decimal(response_data["items"][0]["taxful_base_unit_price"]) == Decimal(product_price).quantize(precision)
        assert Decimal(response_data["items"][0]["taxful_discount_amount"]) == Decimal()
        assert Decimal(response_data["items"][0]["taxful_price"]) == expected_price
        assert Decimal(response_data["items"][0]["taxful_discounted_unit_price"]) == Decimal(product_price).quantize(precision)
        assert Decimal(response_data["items"][0]["tax_amount"]) == Decimal()
        payload = {
            'product': shop_product.product.pk,
            'shop': shop.pk,
        }
        response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.pk, basket.key), payload)
        assert response.status_code == status.HTTP_200_OK
        response_data = json.loads(response.content.decode("utf-8"))
        assert len(response_data["items"]) == 1
        assert not response_data["validation_errors"]
        assert response_data["items"][-1]["text"] == "%s" % shop_product.product.name


@pytest.mark.django_db
def test_add_product_to_basket_with_summary(admin_user):
    tax = get_default_tax()
    tax2 = get_tax("simple-tax-2", "Simple tax 2", Decimal("0.25"))
    create_default_tax_rule(tax2)

    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        shop = factories.get_default_shop()
        basket = factories.get_basket()
        factories.get_default_payment_method()
        factories.get_default_shipping_method()
        shop_product = factories.get_default_shop_product()
        product_price = 1
        shop_product.default_price = TaxfulPrice(product_price, shop.currency)
        shop_product.save()
        client = get_client(admin_user)
        # add shop product
        payload = {
            'shop_product': shop_product.id
        }
        response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.pk, basket.key), payload)
        assert response.status_code == status.HTTP_200_OK
        response_data = json.loads(response.content.decode("utf-8"))

        # Tax summary should not be present here
        assert "summary" not in response_data
        assert "summary" not in response_data["items"][0]

        # Get the tax summary
        response = client.get('/api/shuup/basket/{}-{}/taxes/'.format(shop.pk, basket.key))
        assert response.status_code == status.HTTP_200_OK
        response_data = json.loads(response.content.decode("utf-8"))

        assert "lines" in response_data
        assert "summary" in response_data
        line_summary = response_data["lines"]
        basket_summary = response_data["summary"]
        first_tax_summary = basket_summary[0]
        second_tax_summary = basket_summary[1]

        assert int(first_tax_summary["tax_id"]) == tax.id
        assert int(second_tax_summary["tax_id"]) == tax2.id

        assert first_tax_summary["tax_rate"] == tax.rate
        assert second_tax_summary["tax_rate"] == tax2.rate

        first_line_summary = line_summary[0]
        second_line_summary = line_summary[1]
        assert "tax" in first_line_summary
        assert "tax" in second_line_summary


@pytest.mark.django_db
def test_line_not_updated(admin_user):
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        shop = factories.get_default_shop()
        basket = factories.get_basket()
        factories.get_default_payment_method()
        factories.get_default_shipping_method()
        shop_product = factories.get_default_shop_product()
        product_price = 1
        shop_product.default_price = TaxfulPrice(product_price, shop.currency)
        shop_product.save()
        client = get_client(admin_user)
        # just add, should be a new line
        payload = {
            'shop_product': shop_product.id
        }
        response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.pk, basket.key), payload)
        assert response.status_code == status.HTTP_200_OK
        response_data = json.loads(response.content.decode("utf-8"))
        assert len(response_data["items"]) == 1
        assert not response_data["validation_errors"]
        assert float(response_data["total_price"]) == product_price

        # just add, should update the product line
        payload = {
            'shop_product': shop_product.id
        }
        response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.pk, basket.key), payload)
        assert response.status_code == status.HTTP_200_OK
        response_data = json.loads(response.content.decode("utf-8"))
        assert len(response_data["items"]) == 1
        assert not response_data["validation_errors"]
        assert float(response_data["total_price"]) == product_price * 2


@pytest.mark.django_db
def test_add_variation_product_to_basket(admin_user):
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()

        shop = factories.get_default_shop()
        basket = factories.get_basket()
        factories.get_default_payment_method()
        factories.get_default_shipping_method()

        parent = factories.create_product("ComplexVarParent", shop=shop, supplier=factories.get_default_supplier())
        sizes = [("%sL" % ("X" * x)) for x in range(4)]
        for size in sizes:
            child = factories.create_product("ComplexVarChild-%s" % size, shop=shop, supplier=factories.get_default_supplier())
            child.link_to_parent(parent, variables={"size": size})

        parent_shop_product = parent.get_shop_instance(shop)
        parent_shop_product.refresh_from_db()

        client = get_client(admin_user)

        # add parent shop product
        payload = {
            'shop_product': parent_shop_product.id
        }
        response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.pk, basket.key), payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # add children shop product
        children_shop_product = parent_shop_product.product.variation_children.first().get_shop_instance(shop)
        payload = {
            'shop_product': children_shop_product.pk,
        }
        response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.pk, basket.key), payload)
        assert response.status_code == status.HTTP_200_OK
        response_data = json.loads(response.content.decode("utf-8"))
        assert len(response_data["items"]) == 1
        assert not response_data["validation_errors"]


@pytest.mark.django_db
def test_add_product_shop_mismatch(admin_user):
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        shop = factories.get_default_shop()
        shop2 = create_shop("foobar")
        basket = factories.get_basket()
        factories.get_default_payment_method()
        factories.get_default_shipping_method()
        sp = factories.create_product("test", shop=shop2, supplier=factories.get_default_supplier()).get_shop_instance(shop2)
        client = get_client(admin_user)
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
def test_product_is_required_when_adding(admin_user):
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        shop = factories.get_default_shop()
        basket = factories.get_basket()
        shop_product = factories.get_default_shop_product()
        client = get_client(admin_user)
        payload = {
            'shop': shop.id,
        }
        response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.id, basket.key), payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert '"product"' in str(response.content)


@pytest.mark.django_db
def test_quantity_has_to_be_in_stock(admin_user):
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        from shuup_tests.simple_supplier.utils import get_simple_supplier
        shop = factories.get_default_shop()
        basket = factories.get_basket()

        supplier = get_simple_supplier(stock_managed=True)
        product = factories.create_product("simple-test-product", shop, supplier)
        quantity = 256
        supplier.adjust_stock(product.pk, quantity)
        shop_product = product.shop_products.first()
        shop_product.suppliers = [supplier]

        client = get_client(admin_user)
        payload = {
            'shop': shop.id,
            'product': product.id,
            'quantity': 493020
        }
        response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.pk, basket.key), payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert '"Insufficient stock"' in str(response.content)


@pytest.mark.django_db
def test_product_has_to_exist(admin_user):
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        shop = factories.get_default_shop()
        basket = factories.get_basket()
        client = get_client(admin_user)
        # invalid product
        payload = {
            'shop': shop.id,
            'product': 2384958,
        }
        response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.pk, basket.key), payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Product does not exist" in str(response.content)

        # invalid shop product
        payload = {
            'shop_product': 2384958
        }
        response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.pk, basket.key), payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Product does not exist" in str(response.content)


@pytest.mark.django_db
def test_update_line_quantity(admin_user):
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        shop = factories.get_default_shop()
        basket = factories.get_basket()
        factories.get_default_payment_method()
        factories.get_default_shipping_method()
        shop_product = factories.get_default_shop_product()
        shop_product.default_price = TaxfulPrice(1, shop.currency)
        shop_product.save()
        client = get_client(admin_user)
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
def test_basket_can_be_cleared(admin_user):
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        shop = factories.get_default_shop()
        basket = factories.get_basket()
        shop_product = factories.get_default_shop_product()
        client = get_client(admin_user)
        payload = {
            'shop': shop.id,
            'product': shop_product.product.id,
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
def test_can_delete_line(admin_user):
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        shop = factories.get_default_shop()
        basket = factories.get_basket()
        shop_product = factories.get_default_shop_product()
        client = get_client(admin_user)
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
def test_add_blank_code(admin_user):
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        shop = factories.get_default_shop()
        basket = factories.get_basket()
        shop_product = factories.get_default_shop_product()
        client = get_client(admin_user)
        payload = {
            'code': ''
        }
        response = client.post('/api/shuup/basket/{}-{}/add_code/'.format(shop.pk, basket.key), payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = json.loads(response.content.decode("utf-8"))
        assert 'code' in response_data


@pytest.mark.django_db
def test_cant_add_a_dummy_campaign_code(admin_user):
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        shop = factories.get_default_shop()
        basket = factories.get_basket()
        factories.get_default_shop_product()
        client = get_client(admin_user)
        payload = {
            'code': 'ABCDE'
        }
        response = client.post('/api/shuup/basket/{}-{}/add_code/'.format(shop.pk, basket.key), payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_cant_remove_a_dummy_campaign_code(admin_user):
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        shop = factories.get_default_shop()
        basket = factories.get_basket()
        factories.get_default_shop_product()
        client = get_client(admin_user)
        payload = {
            'code': 'ABCDE'
        }
        response = client.post('/api/shuup/basket/{}-{}/remove_code/'.format(shop.pk, basket.key), payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_cant_clear_dummy_campaign_codes(admin_user):
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        shop = factories.get_default_shop()
        basket = factories.get_basket()
        factories.get_default_shop_product()
        client = get_client(admin_user)
        response = client.post('/api/shuup/basket/{}-{}/clear_codes/'.format(shop.pk, basket.key))
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_can_add_remove_a_valid_campaign_code(admin_user):
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        shop = factories.get_default_shop()
        basket = factories.get_basket()
        factories.get_default_shop_product()
        client = get_client(admin_user)

        coupon = Coupon.objects.create(code="DACODE", active=True)
        get_default_campaign(coupon)

        payload = {
            'code': 'DACODE'
        }
        response = client.post('/api/shuup/basket/{}-{}/add_code/'.format(shop.pk, basket.key), payload)
        basket_data = json.loads(response.content.decode("utf-8"))
        assert response.status_code == status.HTTP_200_OK
        assert 'DACODE' in basket_data['codes']

        response = client.post('/api/shuup/basket/{}-{}/remove_code/'.format(shop.pk, basket.key), payload)
        basket_data = json.loads(response.content.decode("utf-8"))
        assert response.status_code == status.HTTP_200_OK
        assert len(basket_data['codes']) == 0


@pytest.mark.django_db
def test_can_clear_valid_campaign_codes(admin_user):
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        shop = factories.get_default_shop()
        basket = factories.get_basket()
        factories.get_default_shop_product()
        client = get_client(admin_user)

        coupon1 = Coupon.objects.create(code="DACODE", active=True)
        get_default_campaign(coupon1)
        coupon2 = Coupon.objects.create(code="SUPERCODE2", active=True)
        get_default_campaign(coupon2)

        # add first code
        payload = {'code': 'DACODE'}
        response = client.post('/api/shuup/basket/{}-{}/add_code/'.format(shop.pk, basket.key), payload)
        basket_data = json.loads(response.content.decode("utf-8"))
        assert response.status_code == status.HTTP_200_OK
        assert 'DACODE' in basket_data['codes']

        # add second code
        payload = {'code': 'SUPERCODE2'}
        response = client.post('/api/shuup/basket/{}-{}/add_code/'.format(shop.pk, basket.key), payload)
        basket_data = json.loads(response.content.decode("utf-8"))
        assert response.status_code == status.HTTP_200_OK
        assert 'SUPERCODE2' in basket_data['codes']

        # clear all codes
        response = client.post('/api/shuup/basket/{}-{}/clear_codes/'.format(shop.pk, basket.key), payload)
        basket_data = json.loads(response.content.decode("utf-8"))
        assert response.status_code == status.HTTP_200_OK
        assert len(basket_data['codes']) == 0


@pytest.mark.django_db
def test_multiple_coupons_work_properly(admin_user):
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        shop = factories.get_default_shop()
        basket = factories.get_basket()
        factories.get_default_shop_product()
        client = get_client(admin_user)

        code_one = "DACODE"
        code_two = "DACODE1"
        coupon = Coupon.objects.create(code=code_one, active=True)
        get_default_campaign(coupon)

        payload = {
            'code': code_one
        }
        response = client.post('/api/shuup/basket/{}-{}/add_code/'.format(shop.pk, basket.key), payload)
        basket_data = json.loads(response.content.decode("utf-8"))
        assert response.status_code == status.HTTP_200_OK
        assert code_one in basket_data['codes']

        coupon1 = Coupon.objects.create(code=code_two, active=True)
        get_default_campaign(coupon1)
        payload = {
            'code': code_two
        }
        response = client.post('/api/shuup/basket/{}-{}/add_code/'.format(shop.pk, basket.key), payload)
        basket_data = json.loads(response.content.decode("utf-8"))
        assert response.status_code == status.HTTP_200_OK
        assert code_two in basket_data['codes']
        assert len(basket_data["codes"]) == 2


@pytest.mark.django_db
def test_set_shipping_address(admin_user):
    with override_settings(**REQUIRED_SETTINGS):
        shop = factories.get_default_shop()
        basket = factories.get_basket()
        factories.get_default_payment_method()
        factories.get_default_shipping_method()
        client = get_client(admin_user)
        addr1 = factories.get_address()
        addr1.save()

        # use existing address
        payload = {
            'id': addr1.id
        }
        response = client.post('/api/shuup/basket/{}-{}/set_shipping_address/'.format(shop.pk, basket.key), payload)
        assert response.status_code == status.HTTP_200_OK
        response_data = json.loads(response.content.decode("utf-8"))
        shipping_addr = response_data["shipping_address"]
        assert shipping_addr["id"] == addr1.id
        assert shipping_addr["prefix"] == addr1.prefix
        assert shipping_addr["name"] == addr1.name
        assert shipping_addr["postal_code"] == addr1.postal_code
        assert shipping_addr["street"] == addr1.street
        assert shipping_addr["city"] == addr1.city
        assert shipping_addr["country"] == addr1.country

        # create a new address
        address_data = {
            'name': 'name',
            'prefix': 'prefix',
            'postal_code': 'postal_code',
            'street': 'street',
            'city': 'city',
            'country': 'BR'
        }
        response = client.post('/api/shuup/basket/{}-{}/set_shipping_address/'.format(shop.pk, basket.key), address_data)
        assert response.status_code == status.HTTP_200_OK
        response_data = json.loads(response.content.decode("utf-8"))
        shipping_addr = response_data["shipping_address"]
        assert shipping_addr["id"] == addr1.id+1
        assert shipping_addr["prefix"] == address_data["prefix"]
        assert shipping_addr["name"] == address_data["name"]
        assert shipping_addr["postal_code"] == address_data["postal_code"]
        assert shipping_addr["street"] == address_data["street"]
        assert shipping_addr["city"] == address_data["city"]
        assert shipping_addr["country"] == address_data["country"]

        # get the basket and check the address
        response = client.get('/api/shuup/basket/{}-{}/'.format(shop.pk, basket.key))
        assert response.status_code == status.HTTP_200_OK
        response_data = json.loads(response.content.decode("utf-8"))
        shipping_addr = response_data["shipping_address"]
        assert shipping_addr["id"] == addr1.id+1
        assert shipping_addr["prefix"] == address_data["prefix"]
        assert shipping_addr["name"] == address_data["name"]
        assert shipping_addr["postal_code"] == address_data["postal_code"]
        assert shipping_addr["street"] == address_data["street"]
        assert shipping_addr["city"] == address_data["city"]
        assert shipping_addr["country"] == address_data["country"]


@pytest.mark.django_db
def test_abandoned_baskets(admin_user):
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        shop = factories.get_default_shop()
        factories.get_default_payment_method()
        factories.get_default_shipping_method()

        basket1 = factories.get_basket()

        shop_product = factories.get_default_shop_product()
        shop_product.default_price = TaxfulPrice(1, shop.currency)
        shop_product.save()
        client = get_client(admin_user)
        # add shop product
        payload = {'shop_product': shop_product.id}
        response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.pk, basket1.key), payload)
        assert response.status_code == status.HTTP_200_OK
        response_data = json.loads(response.content.decode("utf-8"))
        assert len(response_data["items"]) == 1
        assert response_data["items"][0]["shop_product"] == shop_product.pk
        assert not response_data["validation_errors"]
        assert float(response_data["total_price"]) == 1
        assert Basket.objects.count() == 1

        response = client.get("/api/shuup/basket/abandoned/", format="json", data={
            "shop": shop.pk,
            "days_ago": 0,
            "not_updated_in_hours": 0
        })
        assert response.status_code == status.HTTP_200_OK
        response_data = response.data
        assert len(response_data) == 1
        basket_data = response_data[0]
        assert basket_data["id"] == basket1.id

        basket2 = factories.get_basket()
        response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.pk, basket2.key), payload)
        assert response.status_code == status.HTTP_200_OK
        response_data = json.loads(response.content.decode("utf-8"))
        assert len(response_data["items"]) == 1
        assert response_data["items"][0]["shop_product"] == shop_product.pk
        assert not response_data["validation_errors"]
        assert float(response_data["total_price"]) == 1
        assert Basket.objects.count() == 2

        response = client.get("/api/shuup/basket/abandoned/", format="json", data={
            "shop": shop.pk,
            "days_ago": 0,
            "not_updated_in_hours": 0
        })
        response_data = response.data
        assert len(response_data) == 2
        basket_data = response_data[1]
        assert basket_data["id"] == basket2.id

        # there is no shop with this id thus it should return 400
        response = client.get("/api/shuup/basket/abandoned/", format="json", data={
            "shop": 2,
            "days_ago": 0,
            "not_updated_in_hours": 0
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST


def get_product(sku, shop):
    product = Product.objects.filter(sku=sku).first()
    if not product:
        product = create_product(sku)
        image = get_random_filer_image()
        media = ProductMedia.objects.create(
            product=product, kind=ProductMediaKind.IMAGE, file=image, enabled=True,
            public=True)
        product.primary_image = media
        product.save()
        assert product.primary_image_id
        sp = ShopProduct.objects.create(
            product=product, shop=shop, visibility=ShopProductVisibility.ALWAYS_VISIBLE
        )
        sp.suppliers.add(get_default_supplier())
    return product


def get_basket(shop):
    import uuid
    return Basket.objects.create(
        key=uuid.uuid1().hex,
        shop=shop,
        prices_include_tax=shop.prices_include_tax,
        currency=shop.currency
    )


def get_user(username, email, password="test"):
    UserModel = django_user_model
    username_field = django_username_field

    try:
        return User._default_manager.get(**{"username": username})
    except User.DoesNotExist:
        kwargs = {
            "email": email,
            "password": password,
            "username": username
        }

        return User._default_manager.create_user(**kwargs)


@pytest.mark.django_db
def test_permissions(admin_user):
    """
     ainoastaan kaupan staff / customer / objektin omistava user
     * voi vaihtaa tilauksen tilan, toisen kaupan staff ei voi vaihtaa tilauksen tilaa
     * retrievaa baskettia kuin sinä itse,
    """
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        shop_one = factories.get_default_shop()
        shop_two = Shop.objects.create(
            name="second shop",
            identifier="second_shop",
            status=ShopStatus.ENABLED,
            public_name="Second shop",
            currency=get_default_currency().code
        )
        user_one = get_user("user_one", "user_one@example.com")
        user_two = get_user("user_two", "user_two@example.com")
        user_three = get_user("user_three", "user_three@example.com")
        user_three.is_staff = True
        user_three.save()

        person_one = factories.create_random_person()
        person_one.user = user_one
        person_one.save()

        person_two = factories.create_random_person()
        person_two.user = user_two
        person_two.save()

        # create products
        product_one = get_product("shop_one_product", shop_one)
        product_two = get_product("shop_two_product", shop_two)

        client = get_client(admin_user)

        response = client.post("/api/shuup/basket/new/", {
            "shop": shop_one.pk,
            "customer": person_one.pk,
        })
        assert response.status_code == status.HTTP_201_CREATED
        basket_data = json.loads(response.content.decode("utf-8"))
        basket = Basket.objects.first()
        assert basket.key == basket_data['uuid'].split("-")[1]
        assert basket.shop == shop_one
        assert basket.creator == admin_user

        response = client.get("/api/shuup/basket/{}-{}/".format(shop_one.pk, basket.key))
        assert response.status_code == status.HTTP_200_OK

        # someone figured out the first param is shop!! oh noes
        client = get_client(user_one)
        response = client.get("/api/shuup/basket/{}-{}/".format(shop_two.pk, basket.key))
        assert response.status_code == status.HTTP_404_NOT_FOUND

        basket = Basket.objects.first()
        assert basket.key == basket_data['uuid'].split("-")[1]
        assert basket.shop == shop_one
        assert basket.creator == admin_user

        # ok, person one has permission to their own basket even though they didn't create it
        basket = assert_basket_retrieve(admin_user, basket, basket_data, person_one, shop_one, status.HTTP_200_OK)

        # Person two is not allowed to see the basket
        basket = assert_basket_retrieve(admin_user, basket, basket_data, person_two, shop_one, status.HTTP_403_FORBIDDEN)

        # but admin is, yay admin!
        basket = assert_basket_retrieve(admin_user, basket, basket_data, admin_user, shop_one, status.HTTP_200_OK)

        # ima become staff. I have the power.
        person_three = factories.create_random_person()
        person_three.user = user_three
        person_three.save()
        shop_one.staff_members.add(person_three.user)

        basket = assert_basket_retrieve(admin_user, basket, basket_data, person_three, shop_one, status.HTTP_200_OK)


@pytest.mark.django_db
def test_anonymous_basket():
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        # create anonymous basket
        shop = factories.get_default_shop()
        client = APIClient()
        response = client.post("/api/shuup/basket/new/", {
            "shop": shop.pk
        })
        basket = Basket.objects.first()
        assert basket
        assert not basket.customer
        assert not basket.orderer
        assert not basket.creator
        basket_data = json.loads(response.content.decode("utf-8"))
        response = client.get("/api/shuup/basket/{}-{}/".format(shop.pk, basket.key))
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_add_product_to_basket_with_custom_shop_product_fields(admin_user):
    with override_settings(**REQUIRED_SETTINGS):
        product_name = "Product Name"
        shop_product_name = "SHOP Product Name"

        set_configuration()
        shop = factories.get_default_shop()
        basket = factories.get_basket()
        factories.get_default_payment_method()
        factories.get_default_shipping_method()
        shop_product = factories.get_default_shop_product()
        shop_product.default_price = TaxfulPrice(1, shop.currency)
        shop_product.save()

        shop_product.product.name = product_name
        shop_product.product.save()
        client = get_client(admin_user)

        payload = {
            'product': shop_product.product.pk,
            'shop': shop.pk
        }
        response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.pk, basket.key), payload)
        assert response.status_code == status.HTTP_200_OK

        response_data = json.loads(response.content.decode("utf-8"))
        assert len(response_data["items"]) == 1
        assert response_data["items"][0]["shop_product"] == shop_product.pk
        assert response_data["items"][0]["text"] == product_name

        # set shop product name
        shop_product.product.name = shop_product_name
        shop_product.product.save()

        # add product
        payload = {
            'product': shop_product.product.pk,
            'shop': shop.pk
        }
        response = client.post('/api/shuup/basket/{}-{}/add/'.format(shop.pk, basket.key), payload)
        assert response.status_code == status.HTTP_200_OK
        response_data = json.loads(response.content.decode("utf-8"))
        assert len(response_data["items"]) == 1
        assert response_data["items"][0]["text"] == shop_product_name


def assert_basket_retrieve(admin_user, basket, data, person, shop, status):
    user = person if isinstance(person, User) else person.user
    client = get_client(user)
    response = client.get("/api/shuup/basket/{}-{}/".format(shop.pk, basket.key))
    assert response.status_code == status
    basket = Basket.objects.first()
    assert basket.key == data['uuid'].split("-")[1]
    assert basket.shop == shop
    assert basket.creator == admin_user
    return basket


@pytest.mark.django_db
def test_basket_with_methods(admin_user):
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        shop = factories.get_default_shop()
        shop2 = create_shop("foobar")
        client = get_client(admin_user)
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
        response = client.post("/api/shuup/basket/new/", {"shop": 1000})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # no shop in multishop mode
        response = client.post("/api/shuup/basket/new/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # no shop in single shop mode
        with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=False):
            response = client.post("/api/shuup/basket/new/")
            assert response.status_code == status.HTTP_201_CREATED
            basket_data = json.loads(response.content.decode("utf-8"))
            basket = Basket.objects.all()[1]
            assert basket.key == basket_data['uuid'].split("-")[1]
            assert basket.shop == shop
            assert basket.creator == admin_user

            person = factories.create_random_person()

            response = client.post("/api/shuup/basket/new/", data={"customer": person.pk})
            assert response.status_code == status.HTTP_201_CREATED
            basket_data = json.loads(response.content.decode("utf-8"))
            basket = Basket.objects.all()[2]
            assert basket.key == basket_data['uuid'].split("-")[1]
            assert basket.shop == shop
            assert basket.creator == admin_user
            assert basket.customer.pk == person.pk

            # Set payment method for basket
            payment_method = factories.get_default_payment_method()
            data = {"id": payment_method.id}
            response = client.post('/api/shuup/basket/{}-{}/set_payment_method/'.format(shop.pk, basket.key), data)
            assert response.status_code == status.HTTP_200_OK
            response_data = json.loads(response.content.decode("utf-8"))
            method_data = response_data["payment_method"]
            assert method_data["id"] == payment_method.id
            assert method_data["translations"]["en"]["name"] == payment_method.name
            assert method_data["price"] == 0

            # Set shipping method for basket
            shipping_price = 72
            shipping_method = factories.get_shipping_method(shop, price=shipping_price)
            data = {"id": shipping_method.id}
            response = client.post('/api/shuup/basket/{}-{}/set_shipping_method/'.format(shop.pk, basket.key), data)
            assert response.status_code == status.HTTP_200_OK
            response_data = json.loads(response.content.decode("utf-8"))
            method_data = response_data["shipping_method"]
            assert method_data["id"] == shipping_method.id
            assert method_data["translations"]["en"]["name"] == shipping_method.name
            assert method_data["price"] == shipping_price
            assert method_data["is_available"] == True

            # Make sure that the retrieved basket also has correct methods
            response = client.get("/api/shuup/basket/{}-{}/".format(shop.pk, basket.key))
            assert response.status_code == 200
            response_data = json.loads(response.content.decode("utf-8"))
            assert response_data["shipping_method"]["id"] == shipping_method.id
            assert response_data["payment_method"]["id"] == payment_method.id

            # Unset payment method
            response = client.post('/api/shuup/basket/{}-{}/set_payment_method/'.format(shop.pk, basket.key), {})
            assert response.status_code == status.HTTP_200_OK
            response_data = json.loads(response.content.decode("utf-8"))
            assert response_data.get("payment_method") is None

            # Make sure that the retrieved basket also has correct method
            response = client.get("/api/shuup/basket/{}-{}/".format(shop.pk, basket.key))
            assert response.status_code == 200
            response_data = json.loads(response.content.decode("utf-8"))
            assert response_data["shipping_method"]["id"] == shipping_method.id
            assert response_data.get("payment_method") is None

            # Unset shipping method
            response = client.post('/api/shuup/basket/{}-{}/set_shipping_method/'.format(shop.pk, basket.key), {})
            assert response.status_code == status.HTTP_200_OK
            response_data = json.loads(response.content.decode("utf-8"))
            assert response_data.get("shipping_method") is None

            # Make sure that the retrieved basket also has correct method
            response = client.get("/api/shuup/basket/{}-{}/".format(shop.pk, basket.key))
            assert response.status_code == 200
            response_data = json.loads(response.content.decode("utf-8"))
            assert response_data.get("payment_method") is None
            assert response_data.get("shipping_method") is None


@pytest.mark.parametrize("prices_include_tax, tax_rate, product_price, expected_taxful_price, expected_taxless_price", [
    (True, 0, 50, 50, 50),
    (False, 0, 50, 50, 50),
    (True, 0.1, 100, 100, 90.91),
    (False, 0.1, 100, 110, 100)
])
@pytest.mark.django_db
def test_basket_taxes(admin_user, prices_include_tax, tax_rate, product_price, expected_taxful_price, expected_taxless_price):
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        shop = factories.get_shop(prices_include_tax, enabled=True)
        factories.get_payment_method(shop)
        factories.get_shipping_method(shop)
        product = factories.create_product("product", shop, factories.get_default_supplier(), product_price)
        shop_product = product.shop_products.filter(shop=shop).first()
        client = get_client(admin_user)

        tax = factories.get_default_tax()
        tax.rate = Decimal(tax_rate)
        tax.save()

        response = client.post("/api/shuup/basket/new/", {"shop": shop.pk}, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        basket_key = response.data['uuid']

        response = client.post('/api/shuup/basket/%s/add/' % basket_key, {'shop_product': shop_product.id}, format="json")
        assert response.status_code == status.HTTP_200_OK

        precision = Decimal("0.01")
        data = response.data
        assert len(data["items"]) == 1
        assert data["items"][0]["shop_product"] == shop_product.pk
        assert not data["validation_errors"]
        assert Decimal(data["items"][0]["quantity"]) == Decimal(1)
        assert Decimal(data["items"][0]["taxful_price"]).quantize(precision) == Decimal(expected_taxful_price).quantize(precision)
        assert Decimal(data["items"][0]["taxless_price"]).quantize(precision) == Decimal(expected_taxless_price).quantize(precision)
        assert Decimal(data["taxful_total_price"]).quantize(precision) == Decimal(expected_taxful_price).quantize(precision)
        assert Decimal(data["taxless_total_price"]).quantize(precision) == Decimal(expected_taxless_price).quantize(precision)


@pytest.mark.parametrize("currency, currency_decimals", [
    ("USD", 2),
    ("BRL", 2),
    ("GBP", 2),
    ("USD", 2),
    ("IDR", 0),
    ("LYD", 3)
])
@pytest.mark.django_db
def test_basket_taxes_2(admin_user, currency, currency_decimals):
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        shop = factories.get_shop(enabled=True, currency=currency)
        factories.get_payment_method(shop)
        factories.get_shipping_method(shop)
        client = get_client(admin_user)

        Currency.objects.update_or_create(code=currency, defaults={"decimal_places": currency_decimals})

        response = client.post("/api/shuup/basket/new/", {"shop": shop.pk}, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        data = response.data
        assert shop.currency == data["currency"]["code"]
        assert data["currency"]["symbol"] == babel.numbers.get_currency_symbol(shop.currency, get_current_babel_locale())
        assert data["currency"]["decimal_places"] == currency_decimals


@pytest.mark.parametrize("user_mode", ["admin", "staff", "normal", "company"])
@pytest.mark.django_db
def test_create_with_customer(admin_user, user_mode):
    """
    Create the basket with a specified customer
    """
    set_configuration()
    with override_settings(**REQUIRED_SETTINGS):
        shop = factories.get_default_shop()
        factories.get_default_payment_method()
        factories.get_default_shipping_method()

        if user_mode == "admin":
            user = admin_user
            customer = factories.create_random_person()

        elif user_mode == "staff":
            staff = factories.create_random_user(is_staff=True)
            shop.staff_members.add(staff)
            user = staff
            customer = factories.create_random_person()

        elif user_mode == "normal":
            user = factories.create_random_user()
            customer = factories.create_random_person()

        elif user_mode == "company":
            user = factories.create_random_user()
            customer = factories.create_random_company()
            customer.members.add(get_person_contact(user))

        else:
            raise Exception("It should never enter here!")

        client = get_client(user)

        response = client.post("/api/shuup/basket/new/", {"shop": shop.pk, "customer": customer.id}, format="json")
        if user_mode == "normal":
            assert response.status_code == status.HTTP_403_FORBIDDEN
        else:
            assert response.status_code == status.HTTP_201_CREATED
            assert response.data["customer"]["id"] == customer.id


@pytest.mark.parametrize("user_mode", ["admin", "staff", "normal"])
@pytest.mark.django_db
def test_set_customer(admin_user, user_mode):
    """
    Set the basket customer
    """
    set_configuration()
    with override_settings(**REQUIRED_SETTINGS):
        shop = factories.get_default_shop()
        factories.get_default_payment_method()
        factories.get_default_shipping_method()

        customer1 = factories.create_random_person()
        customer2 = factories.create_random_person()

        if user_mode == "admin":
            user = admin_user

        elif user_mode == "staff":
            staff = factories.create_random_user(is_staff=True)
            shop.staff_members.add(staff)
            user = staff

        elif user_mode == "normal":
            user = factories.create_random_user()

        else:
            raise Exception("It should never enter here!")

        client = get_client(user)

        # create basket with the current user customer
        response = client.post("/api/shuup/basket/new/", {"shop": shop.pk}, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        uuid = response.data["uuid"]
        assert response.data["customer"]["id"] == get_person_contact(user).id

        # change the customer
        response = client.post('/api/shuup/basket/%s/set_customer/' % uuid, format="json", data={
            "customer": customer1.id
        })
        if user_mode == "normal":
            assert response.status_code == status.HTTP_403_FORBIDDEN
        else:
            assert response.status_code == status.HTTP_200_OK
            assert response.data["customer"]["id"] == customer1.id

        # change the customer again
        response = client.post('/api/shuup/basket/%s/set_customer/' % uuid, format="json", data={
            "customer": customer2.id
        })
        # nornal user can not change the customer
        if user_mode == "normal":
            assert response.status_code == status.HTTP_403_FORBIDDEN
        else:
            assert response.status_code == status.HTTP_200_OK
            assert response.data["customer"]["id"] == customer2.id

        # change the customer to anonymous
        response = client.post('/api/shuup/basket/%s/set_customer/' % uuid, format="json", data={
            "customer": None
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data["customer"] is None


@pytest.mark.django_db
def test_set_company_customer(admin_user):
    """
    Set the basket customer
    """
    set_configuration()
    with override_settings(**REQUIRED_SETTINGS):
        shop = factories.get_default_shop()
        factories.get_default_payment_method()
        factories.get_default_shipping_method()

        company1 = factories.create_random_company()
        company2 = factories.create_random_company()
        company3 = factories.create_random_company()

        user = factories.create_random_user()

        # the current user controls the company2 and company3
        company2.members.add(get_person_contact(user))
        company3.members.add(get_person_contact(user))

        client = get_client(user)

        # create basket, the customer will be the first attached company
        response = client.post("/api/shuup/basket/new/", {"shop": shop.pk}, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        uuid = response.data["uuid"]
        assert response.data["customer"]["id"] == company2.id

        # change the customer to company
        response = client.post('/api/shuup/basket/%s/set_customer/' % uuid, format="json", data={
            "customer": company2.id
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data["customer"]["id"] == company2.id

        # change the customer to company1
        response = client.post('/api/shuup/basket/%s/set_customer/' % uuid, format="json", data={
            "customer": company1.id
        })
        # user can not change the customer to a non controlled company
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_set_customer_group_prices(admin_user):
    """
    Set the customer to the basket and prices should change
    accordingly to the customer group
    """
    set_configuration()
    with override_settings(**REQUIRED_SETTINGS):
        shop = factories.get_default_shop()
        factories.get_default_payment_method()
        factories.get_default_shipping_method()

        normal_price = Decimal(34)
        discounted_price = Decimal(10)

        product = factories.create_product("product", shop, factories.get_default_supplier(), normal_price)

        # customer1 in group1
        group1 = factories.create_random_contact_group()
        customer1 = factories.create_random_person()
        customer1.groups.add(group1)

        # customer2 in group2
        group2 = factories.create_random_contact_group()
        customer2 = factories.create_random_person()
        customer2.groups.add(group2)

        # group2 has discounts in product
        from shuup.customer_group_pricing.models import CgpPrice
        CgpPrice.objects.create(product=product, shop=shop, group=group2, price_value=discounted_price)

        client = get_client(admin_user)

        # create basket with the current user customer
        response = client.post("/api/shuup/basket/new/", {"shop": shop.pk}, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        uuid = response.data["uuid"]
        assert response.data["customer"]["id"] == get_person_contact(admin_user).id

        from shuup.core.pricing._context import PricingContext
        context1 = PricingContext(shop=shop, customer=customer1)
        context2 = PricingContext(shop=shop, customer=customer2)

        assert product.get_price(context1).value == normal_price
        assert product.get_price(context2).value == discounted_price

        # add the product
        response = client.post('/api/shuup/basket/%s/add/' % uuid, format="json", data={
            "shop": shop.id,
            "product": product.id
        })
        assert response.status_code == status.HTTP_200_OK
        product_line = [line for line in response.data["items"] if line["type"] == OrderLineType.PRODUCT.value][0]
        assert Decimal(product_line["price"]) == normal_price

        # set customer1
        response = client.post('/api/shuup/basket/%s/set_customer/' % uuid, format="json", data={
            "customer": customer1.id
        })
        assert response.status_code == status.HTTP_200_OK
        product_line = [line for line in response.data["items"] if line["type"] == OrderLineType.PRODUCT.value][0]
        assert Decimal(product_line["price"]) == normal_price

        # set customer2, new price
        response = client.post('/api/shuup/basket/%s/set_customer/' % uuid, format="json", data={
            "customer": customer2.id
        })
        assert response.status_code == status.HTTP_200_OK
        product_line = [line for line in response.data["items"] if line["type"] == OrderLineType.PRODUCT.value][0]
        assert Decimal(product_line["price"]) == discounted_price


@pytest.mark.django_db
def test_set_customer_campaigns(admin_user):
    """
    Set the customer to the basket and prices should change
    accordingly to the rules
    """
    set_configuration()
    with override_settings(**REQUIRED_SETTINGS):
        shop = factories.get_default_shop()
        factories.get_default_payment_method()
        factories.get_default_shipping_method()

        normal_price = Decimal(34)
        discounted_price = Decimal(10)

        product = factories.create_product("product", shop, factories.get_default_supplier(), normal_price)

        # customer1 in group1
        group1 = factories.create_random_contact_group()
        customer1 = factories.create_random_person()
        customer1.groups.add(group1)

        # customer2 in group2
        group2 = factories.create_random_contact_group()
        customer2 = factories.create_random_person()
        customer2.groups.add(group2)

        # group2 has discounts in product
        from shuup.campaigns.models import BasketCampaign
        from shuup.campaigns.models.basket_line_effects import DiscountFromProduct
        from shuup.campaigns.models.basket_conditions import ContactGroupBasketCondition

        # only affects group2
        condition = ContactGroupBasketCondition.objects.create()
        condition.contact_groups.add(group2)

        campaign = BasketCampaign.objects.create(
            shop=shop,
            name="campaign",
            basket_line_text="test",
            active=True,
            start_datetime=now() - timedelta(days=1),
            end_datetime=now() + timedelta(days=1)
        )
        campaign.conditions.add(condition)

        # set the discount effect
        effect = DiscountFromProduct.objects.create(
            campaign=campaign,
            discount_amount=(normal_price-discounted_price)
        )
        effect.products.add(product)

        client = get_client(admin_user)

        # create basket with the current user customer
        response = client.post("/api/shuup/basket/new/", {"shop": shop.pk}, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        uuid = response.data["uuid"]
        assert response.data["customer"]["id"] == get_person_contact(admin_user).id

        # add the product
        response = client.post('/api/shuup/basket/%s/add/' % uuid, format="json", data={
            "shop": shop.id,
            "product": product.id
        })
        assert response.status_code == status.HTTP_200_OK
        product_line = [line for line in response.data["items"] if line["type"] == OrderLineType.PRODUCT.value][0]
        assert Decimal(product_line["price"]) == normal_price

        # set customer1
        response = client.post('/api/shuup/basket/%s/set_customer/' % uuid, format="json", data={
            "customer": customer1.id
        })
        assert response.status_code == status.HTTP_200_OK
        product_line = [line for line in response.data["items"] if line["type"] == OrderLineType.PRODUCT.value][0]
        assert Decimal(product_line["price"]) == normal_price

        # set customer2, new price
        response = client.post('/api/shuup/basket/%s/set_customer/' % uuid, format="json", data={
            "customer": customer2.id
        })
        assert response.status_code == status.HTTP_200_OK
        product_line = [line for line in response.data["items"] if line["type"] == OrderLineType.PRODUCT.value][0]
        assert Decimal(product_line["price"]) == discounted_price


@pytest.mark.parametrize("with_admin", [False, True])
@pytest.mark.django_db
def test_anonymous(admin_user, with_admin):
    """
    Create order with anonymous user
    """
    set_configuration()
    with override_settings(**REQUIRED_SETTINGS):
        shop = factories.get_default_shop()
        factories.get_default_payment_method()
        factories.get_default_shipping_method()
        OrderStatusManager().ensure_default_statuses()

        product = factories.create_product("product", shop, factories.get_default_supplier(), "10")
        client = APIClient()

        if with_admin:
            user = admin_user
            client.force_authenticate(admin_user)
        else:
            user = AnonymousUser()

        payload = {"shop": shop.pk}
        if with_admin:
            payload["customer"] = None

        response = client.post("/api/shuup/basket/new/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        uuid = response.data["uuid"]
        assert response.data["customer"] is None

        # add the product
        response = client.post('/api/shuup/basket/%s/add/' % uuid, format="json", data={
            "shop": shop.id,
            "product": product.id
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data["customer"] is None

        # create the order
        response = client.post('/api/shuup/basket/%s/create_order/' % uuid, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        order = Order.objects.get(id=response.data["id"])
        assert order.customer is None
        if with_admin:
            assert order.creator == user
            assert order.orderer is None
        else:
            assert order.creator is None
            assert order.orderer is None
