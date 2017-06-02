# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json
from decimal import Decimal

import pytest
import six
from django.contrib.auth.models import User
from pytest_django.fixtures import django_user_model, django_username_field
from rest_framework import status
from rest_framework.test import APIClient

from shuup import configuration
from shuup.core import cache
from shuup.core.models import (
    Basket, get_person_contact, Order, OrderStatus, PaymentStatus, Product,
    ProductMedia, ProductMediaKind, ProductVariationVariable, ShippingStatus,
    Shop, ShopProduct, ShopProductVisibility, ShopStatus
)
from shuup.core.pricing import TaxfulPrice
from shuup.testing import factories
from shuup.testing.factories import (
    create_product, create_random_order, get_default_currency,
    get_default_product, get_default_supplier, get_random_filer_image
)
from shuup_tests.campaigns.test_discount_codes import (
    Coupon, get_default_campaign
)


def setup_function(fn):
    cache.clear()

def configure(settings):
    settings.SHUUP_ENABLE_MULTIPLE_SHOPS = True
    settings.SHUUP_BASKET_ORDER_CREATOR_SPEC = (
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
    set_configuration()

def set_configuration():
    config = {
        "api_permission_ShopViewSet": 3,
        "api_permission_TreesAdminShopProductViewSet": 5,
        "api_permission_TreesShopViewSet": 3,
        "api_permission_TreesNotificationViewSet": 4,
        "api_permission_FrontShopProductViewSet": 3,
        "api_permission_PersonContactViewSet": 4,
        "api_permission_TreesAdminShopViewSet": 5,
        "api_permission_TreesShopProductViewSet": 3,
        "api_permission_FrontUserViewSet": 2,
        "api_permission_FrontOrderViewSet": 4,
        "api_permission_SMSPasswordSet": 2,
        "api_permission_AttributeViewSet": 5,
        "api_permission_TaxClassViewSet": 5,
        "api_permission_RequestResetPassword": 5,
        "api_permission_TreesAdminCouponViewSet": 5,
        "api_permission_FrontProductViewSet": 3,
        "api_permission_TreesProductViewSet": 3,
        "api_permission_ProductVariationVariableValueViewSet": 5,
        "api_permission_SalesUnitViewSet": 5,
        "api_permission_UserViewSet": 5,
        "api_permission_ShopReviewViewSet": 4,
        "api_permission_BasketViewSet": 2,
        "api_permission_CategoryViewSet": 1,
        "api_permission_ShipmentViewSet": 5,
        "api_permission_TreesAnalyticsViewSet": 2,
        "api_permission_CgpPriceViewSet": 5,
        "api_permission_VerificationSender": 2,
        "api_permission_ShopProductViewSet": 3,
        "api_permission_TreesAdminOrderViewSet": 5,
        "api_permission_ContactViewSet": 4,
        "api_permission_TreesProductFavoritesViewSet": 4,
        "api_permission_OrderViewSet": 5,
        "api_permission_ProductViewSet": 5,
        "api_permission_CustomerVerificationViewSet": 5,
        "api_permission_ProductTypeViewSet": 5,
        "api_permission_ProductReviewViewSet": 4,
        "api_permission_ProductVariationVariableViewSet": 5,
        "api_permission_VerificationChecker": 4,
        "api_permission_TreesFrontOrderViewSet": 5,
        "api_permission_SupplierViewSet": 5,
        "api_permission_ManufacturerViewSet": 5,
        "api_permission_ProductMediaViewSet": 5,
        "api_permission_TreesShopFavoritesViewSet": 4,
        "api_permission_ProductAttributeViewSet": 5,
        "api_permission_TreesAdminPatientsViewSet": 5,
        "api_permission_MutableAddressViewSet": 5,
        "api_permission_ProductPackageViewSet": 5,
        "api_permission_TreesAdminNotificationViewSet": 5,
        "api_permission_TreesFAQViewSet": 1,
    }
    for field, value in six.iteritems(config):
        configuration.set(None, field, value)


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

    person = factories.create_random_person()

    response = client.post("/api/shuup/basket/new/?customer_id={}".format(person.pk), data={"customer_id": person.pk})
    assert response.status_code == status.HTTP_201_CREATED
    basket_data = json.loads(response.content.decode("utf-8"))
    basket = Basket.objects.all()[2]
    assert basket.key == basket_data['uuid'].split("-")[1]
    assert basket.shop == shop
    assert basket.creator == admin_user
    assert basket.customer.pk == person.pk


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
def test_add_variation_product_to_basket(admin_user, settings):
    configure(settings)
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

    client = _get_client(admin_user)

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
def test_multiple_coupons_work_properly(admin_user, settings):
    configure(settings)
    shop = factories.get_default_shop()
    basket = factories.get_basket()
    shop_product = factories.get_default_shop_product()
    client = _get_client(admin_user)

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
    assert len(basket_data["codes"]) == 1


@pytest.mark.parametrize("target_customer", ["admin", "other"])
@pytest.mark.django_db
def test_create_order(admin_user, settings, target_customer):
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

    if target_customer == "other":
        target = factories.create_random_person()
        payload["customer_id"] = target.pk
    else:
        target = get_person_contact(admin_user)


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
    assert order.customer == target
    assert order.orderer == get_person_contact(admin_user)
    assert order.creator == admin_user
    assert not order.billing_address
    assert not order.shipping_address


@pytest.mark.django_db
def test_set_shipping_address(admin_user):
    shop = factories.get_default_shop()
    basket = factories.get_basket()
    factories.get_default_payment_method()
    factories.get_default_shipping_method()
    client = _get_client(admin_user)
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


def _get_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.mark.django_db
def test_copy_order_to_basket(admin_user, settings):
    configure(settings)
    shop = factories.get_default_shop()
    basket = factories.get_basket()
    p1 = factories.create_product("test", shop=shop, supplier=factories.get_default_supplier())
    order = factories.create_order_with_product(factories.get_default_product(), factories.get_default_supplier(), 2, 10, shop=shop)
    factories.add_product_to_order(order, factories.get_default_supplier(), p1, 2, 5)
    order.customer = get_person_contact(admin_user)
    order.save()
    client = _get_client(admin_user)
    payload = {
        "order": order.pk
    }
    response = client.post('/api/shuup/basket/{}-{}/add_from_order/'.format(shop.pk, basket.key), payload)
    assert response.status_code == status.HTTP_200_OK
    response_data = json.loads(response.content.decode("utf-8"))
    assert len(response_data["items"]) == 2
    assert not response_data["validation_errors"]
    basket.refresh_from_db()
    assert len(basket.data["lines"]) == 2

    # do it again, basket should clear first then read items
    payload = {
        "order": order.pk
    }
    response = client.post('/api/shuup/basket/{}-{}/add_from_order/'.format(shop.pk, basket.key), payload)
    assert response.status_code == status.HTTP_200_OK
    response_data = json.loads(response.content.decode("utf-8"))
    assert len(response_data["items"]) == 2
    assert not response_data["validation_errors"]
    basket.refresh_from_db()
    assert len(basket.data["lines"]) == 2


@pytest.mark.django_db
def test_abandoned_baskets(admin_user, settings):
    configure(settings)
    shop = factories.get_default_shop()
    factories.get_default_payment_method()
    factories.get_default_shipping_method()

    basket1 = factories.get_basket()

    shop_product = factories.get_default_shop_product()
    shop_product.default_price = TaxfulPrice(1, shop.currency)
    shop_product.save()
    client = _get_client(admin_user)
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

    response = client.get("/api/shuup/basket/abandoned/?shop={}&days_ago=0&not_updated_in_hours=0".format(shop.pk))
    response_data = json.loads(response.content.decode("utf-8"))
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

    response = client.get("/api/shuup/basket/abandoned/?shop={}&days_ago=0&not_updated_in_hours=0".format(shop.pk))
    response_data = json.loads(response.content.decode("utf-8"))
    assert len(response_data) == 2
    basket_data = response_data[1]
    assert basket_data["id"] == basket2.id

    # there is no shop with this id thus it should return 404
    response = client.get("/api/shuup/basket/abandoned/?shop=2&days_ago=0&not_updated_in_hours=0")
    assert response.status_code == status.HTTP_404_NOT_FOUND


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
def test_permissions(admin_user, settings):
    """
     ainoastaan kaupan staff / customer / objektin omistava user
     * voi vaihtaa tilauksen tilan, toisen kaupan staff ei voi vaihtaa tilauksen tilaa
     * retrievaa baskettia kuin sinä itse,
    """
    configure(settings)
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

    client = _get_client(admin_user)

    response = client.post("/api/shuup/basket/new/", {
        "shop": shop_one.pk,
        "customer_id": person_one.pk,
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
    client = _get_client(user_one)
    response = client.get("/api/shuup/basket/{}-{}/".format(shop_two.pk, basket.key))
    assert response.status_code == status.HTTP_403_FORBIDDEN

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
def test_anonymous_basket(settings):
    configure(settings)
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
def test_add_product_to_basket_with_custom_shop_product_fields(admin_user, settings):
    product_name = "Product Name"
    shop_product_name = "SHOP Product Name"

    configure(settings)
    shop = factories.get_default_shop()
    basket = factories.get_basket()
    factories.get_default_payment_method()
    factories.get_default_shipping_method()
    shop_product = factories.get_default_shop_product()
    shop_product.default_price = TaxfulPrice(1, shop.currency)
    shop_product.save()

    shop_product.product.name = product_name
    shop_product.product.save()
    client = _get_client(admin_user)

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
    client = _get_client(user)
    response = client.get("/api/shuup/basket/{}-{}/".format(shop.pk, basket.key))
    assert response.status_code == status
    basket = Basket.objects.first()
    assert basket.key == data['uuid'].split("-")[1]
    assert basket.shop == shop
    assert basket.creator == admin_user
    return basket


@pytest.mark.django_db
def test_basket_with_methods(admin_user, settings):
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

    person = factories.create_random_person()

    response = client.post("/api/shuup/basket/new/?customer_id={}".format(person.pk), data={"customer_id": person.pk})
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


@pytest.mark.django_db
def test_basket_with_staff_user(settings):
    configure(settings)
    shop = factories.get_default_shop()
    staff_user = User.objects.create(username="staff", is_staff=True)

    client = _get_client(staff_user)
    person = factories.create_random_person()
    response = client.post(
        "/api/shuup/basket/new/?customer_id={}".format(person.pk),
        data={"shop": shop.pk, "customer_id": person.pk})
    # Only stuff linked to shop can create baskets for someone else
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Can still add personal baskets
    staff_person = get_person_contact(staff_user)
    response = client.post(
        "/api/shuup/basket/new/?customer_id={}".format(staff_person.pk),
        data={"shop": shop.pk, "customer_id": staff_person.pk})
    assert response.status_code == status.HTTP_201_CREATED
    basket_data = json.loads(response.content.decode("utf-8"))
    basket = Basket.objects.filter(key=basket_data["uuid"].split("-")[1]).first()
    assert basket.shop == shop
    assert basket.creator == staff_user
    assert basket.customer.pk == staff_person.pk
    response = client.get("/api/shuup/basket/{}/".format(basket_data["uuid"]))
    assert response.status_code == 200

    basket_uuid = basket_data["uuid"]
    assert basket_data['customer']['id'] == staff_person.pk
    assert basket_data['customer']['user'] == staff_user.pk

    # retrieve the basket
    response = client.get("/api/shuup/basket/{}/".format(basket_uuid))
    basket_data = json.loads(response.content.decode("utf-8"))
    assert basket_data['customer']['id'] == staff_person.pk
    assert basket_data['customer']['user'] == staff_user.pk

    # Ok let's link the staff member to the shop and
    # the basket create for random person should work
    shop.staff_members.add(staff_user)
    response = client.post(
        "/api/shuup/basket/new/?customer_id={}".format(person.pk),
        data={"shop": shop.pk, "customer_id": person.pk})
    assert response.status_code == status.HTTP_201_CREATED
    basket_data = json.loads(response.content.decode("utf-8"))
    basket = Basket.objects.filter(key=basket_data["uuid"].split("-")[1]).first()
    assert basket.shop == shop
    assert basket.creator == staff_user
    assert basket.customer.pk == person.pk
    response = client.get("/api/shuup/basket/{}/".format(basket_data["uuid"]))
    assert response.status_code == 200

    basket_uuid = basket_data["uuid"]
    assert basket_data['customer']['id'] == person.pk
    assert basket_data['customer']['user'] is None

    # retrieve the basket
    response = client.get("/api/shuup/basket/{}/".format(basket_uuid))
    basket_data = json.loads(response.content.decode("utf-8"))
    assert basket_data['customer']['id'] == person.pk
    assert basket_data['customer']['user'] is None


@pytest.mark.django_db
def test_basket_reorder_staff_user(settings):
    configure(settings)
    shop = factories.get_default_shop()
    factories.get_default_payment_method()
    factories.get_default_shipping_method()
    staff_user = User.objects.create(username="staff", is_staff=True)

    client = _get_client(staff_user)
    person = factories.create_random_person()

    # create an order for the person
    product = create_product("product", shop=shop, supplier=get_default_supplier(), default_price='12.4')
    order = create_random_order(customer=person, products=[product], completion_probability=1, shop=shop)

    # create the basket
    response = client.post("/api/shuup/basket/new/", data={"shop": shop.pk, "customer_id": person.pk}, format="json")
    # Only stuff linked to shop can create baskets for someone else
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Can still add personal baskets
    staff_person = get_person_contact(staff_user)
    response = client.post("/api/shuup/basket/new/", data={"shop": shop.pk, "customer_id": staff_person.pk}, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    basket_data = json.loads(response.content.decode("utf-8"))
    basket = Basket.objects.filter(key=basket_data["uuid"].split("-")[1]).first()
    assert basket.shop == shop
    assert basket.creator == staff_user
    assert basket.customer.pk == staff_person.pk
    response = client.get("/api/shuup/basket/{}/".format(basket_data["uuid"]))
    assert response.status_code == 200

    # Ok let's link the staff member to the shop and
    # the basket create for random person should work
    shop.staff_members.add(staff_user)
    response = client.post("/api/shuup/basket/new/", data={"shop": shop.pk, "customer_id": person.pk}, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    basket_data = json.loads(response.content.decode("utf-8"))
    basket = Basket.objects.filter(key=basket_data["uuid"].split("-")[1]).first()
    assert basket.shop == shop
    assert basket.creator == staff_user
    assert basket.customer.pk == person.pk
    response = client.get("/api/shuup/basket/{}/".format(basket_data["uuid"]))
    assert response.status_code == 200

    # add contents to the basket from a customer order
    response = client.post('/api/shuup/basket/{}-{}/add_from_order/'.format(shop.pk, basket.key), data={"order": order.pk}, format="json")
    assert response.status_code == status.HTTP_200_OK
    basket_data = json.loads(response.content.decode("utf-8"))
    assert len(basket_data['items']) > 0
    assert Decimal(basket_data['taxful_total_price']) == order.taxful_total_price_value

    # finally create the order
    response = client.post('/api/shuup/basket/{}-{}/create_order/'.format(shop.pk, basket.key))
    assert response.status_code == status.HTTP_201_CREATED
    response_data = json.loads(response.content.decode("utf-8"))
    created_order = Order.objects.get(id=response_data['id'])
    assert created_order.customer == person
    assert created_order.creator == staff_user

    # create a second customer
    person2 = factories.create_random_person()
    # create a basket for customer 2 and try to fill with contents of customer 1 order - it should not be possible
    response = client.post("/api/shuup/basket/new/", data={"shop": shop.pk, "customer_id": person2.pk}, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    basket_data = json.loads(response.content.decode("utf-8"))
    basket = Basket.objects.filter(key=basket_data["uuid"].split("-")[1]).first()
    assert basket.shop == shop
    assert basket.creator == staff_user
    assert basket.customer.pk == person2.pk

    # add contents to the basket from customer 1 order - error
    response = client.post('/api/shuup/basket/{}-{}/add_from_order/'.format(shop.pk, basket.key), data={"order": order.pk}, format="json")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert 'invalid order' in response.content.decode("utf-8")
