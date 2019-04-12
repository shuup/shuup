# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json
from decimal import Decimal

import pytest
import six
from django.contrib.auth import get_user_model
from django.test import override_settings
from pytest_django.fixtures import django_user_model, django_username_field
from rest_framework import status
from rest_framework.test import APIClient

from shuup import configuration
from shuup.core import cache
from shuup.core.models import (
    Basket, get_person_contact, Order, OrderStatus, PaymentStatus, Product,
    ProductMedia, ProductMediaKind, ShippingStatus, Shop, ShopProduct,
    ShopProductVisibility, ShopStatus
)
from shuup.core.pricing import TaxfulPrice
from shuup.testing import factories
from shuup.testing.factories import (
    create_product, create_random_order, get_default_currency,
    get_default_supplier, get_random_filer_image
)
from shuup_tests.campaigns.test_discount_codes import (
    Coupon, get_default_campaign
)

User = get_user_model()

REQUIRED_SETTINGS = dict(
    SHUUP_ENABLE_MULTIPLE_SHOPS=True,
    SHUUP_BASKET_ORDER_CREATOR_SPEC="shuup.core.basket.order_creator:BasketOrderCreator",
    SHUUP_BASKET_STORAGE_CLASS_SPEC="shuup.core.basket.storage:DatabaseBasketStorage",
    SHUUP_BASKET_CLASS_SPEC="shuup.core.basket.objects:Basket",
    MIDDLEWARE_CLASSES=[
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.middleware.locale.LocaleMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware'
    ]
)


def setup_function(fn):
    cache.clear()


def set_configuration():
    config = {
        "api_permission_ShopViewSet": 3,
        "api_permission_FrontShopProductViewSet": 3,
        "api_permission_PersonContactViewSet": 4,
        "api_permission_FrontUserViewSet": 2,
        "api_permission_FrontOrderViewSet": 4,
        "api_permission_AttributeViewSet": 5,
        "api_permission_TaxClassViewSet": 5,
        "api_permission_FrontProductViewSet": 3,
        "api_permission_ProductVariationVariableValueViewSet": 5,
        "api_permission_SalesUnitViewSet": 5,
        "api_permission_UserViewSet": 5,
        "api_permission_ShopReviewViewSet": 4,
        "api_permission_BasketViewSet": 2,
        "api_permission_CategoryViewSet": 1,
        "api_permission_ShipmentViewSet": 5,
        "api_permission_CgpPriceViewSet": 5,
        "api_permission_ShopProductViewSet": 3,
        "api_permission_ContactViewSet": 4,
        "api_permission_OrderViewSet": 5,
        "api_permission_ProductViewSet": 5,
        "api_permission_ProductTypeViewSet": 5,
        "api_permission_ProductVariationVariableViewSet": 5,
        "api_permission_SupplierViewSet": 5,
        "api_permission_ManufacturerViewSet": 5,
        "api_permission_ProductMediaViewSet": 5,
        "api_permission_ProductAttributeViewSet": 5,
        "api_permission_MutableAddressViewSet": 5,
        "api_permission_ProductPackageViewSet": 5,
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
def test_create_new_basket(admin_user):
    with override_settings(**REQUIRED_SETTINGS):
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
        admin_contact = get_person_contact(admin_user)
        assert basket.customer == admin_contact
        assert basket.orderer == admin_contact
        assert basket.creator == admin_user

        # invalid shop
        response = client.post("/api/shuup/basket/new/", data={"shop": 1000})
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

            person = factories.create_random_person()

            response = client.post("/api/shuup/basket/new/", data={"customer": person.pk})
            assert response.status_code == status.HTTP_201_CREATED
            basket_data = json.loads(response.content.decode("utf-8"))
            basket = Basket.objects.all()[2]
            assert basket.key == basket_data['uuid'].split("-")[1]
            assert basket.shop == shop
            assert basket.creator == admin_user
            assert basket.customer.pk == person.pk
            assert basket.orderer.pk == person.pk
            assert basket.creator.pk == admin_user.pk

            # Try to fetch the basket as the customer
            user = factories.UserFactory()
            person.user = user
            person.save()
            response = client.get("/api/shuup/basket/{}/".format(basket_data['uuid']))
            assert response.status_code == 200
            customer_basket_data = json.loads(response.content.decode("utf-8"))
            assert basket.key == customer_basket_data['key']  # Still same basket as before
            assert customer_basket_data['customer']['id'] == person.pk  # Still same customer as before


@pytest.mark.parametrize("target_customer", ["admin", "other_person", "company"])
@pytest.mark.django_db
def test_create_order(admin_user, target_customer):
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        factories.create_default_order_statuses()
        shop = factories.get_default_shop()
        client = _get_client(admin_user)

        # Create basket for target customer
        payload = {"shop": shop.pk}
        target = orderer = get_person_contact(admin_user)
        if target_customer == "other_person":
            target = orderer = factories.create_random_person()
            payload["customer"] = target.pk
        elif target_customer == "company":
            target = factories.create_random_company()
            orderer = factories.create_random_person()
            payload.update({
                "customer": target.pk,
                "orderer": orderer.pk
            })
            target.members.add(orderer)

        response = client.post("/api/shuup/basket/new/", payload)
        assert response.status_code == status.HTTP_201_CREATED
        basket_data = json.loads(response.content.decode("utf-8"))
        basket = Basket.objects.first()
        assert basket.key == basket_data["uuid"].split("-")[1]
        assert basket.customer == target
        assert basket.orderer == orderer

        shop_product = factories.get_default_shop_product()
        shop_product.default_price = TaxfulPrice(1, shop.currency)
        shop_product.save()

        # Add shop product to basket
        payload = {"shop_product": shop_product.id}
        response = client.post("/api/shuup/basket/{}-{}/add/".format(shop.pk, basket.key), payload)
        assert response.status_code == status.HTTP_200_OK
        response_data = json.loads(response.content.decode("utf-8"))
        assert len(response_data["items"]) == 1

        # Create order from basket
        response = client.post("/api/shuup/basket/{}-{}/create_order/".format(shop.pk, basket.key), payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = json.loads(response.content.decode("utf-8"))
        assert "errors" in response_data

        factories.get_default_payment_method()
        factories.get_default_shipping_method()
        response = client.post("/api/shuup/basket/{}-{}/create_order/".format(shop.pk, basket.key), payload)
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
        assert order.orderer == orderer
        assert order.creator == admin_user
        assert not order.billing_address
        assert not order.shipping_address

@pytest.mark.django_db
def test_basket_with_staff_user():
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
        shop = factories.get_default_shop()
        staff_user = User.objects.create(username="staff", is_staff=True)

        client = _get_client(staff_user)
        person = factories.create_random_person()
        response = client.post("/api/shuup/basket/new/", data={"shop": shop.pk, "customer": person.pk})
        # Only stuff linked to shop can create baskets for someone else
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Can still add personal baskets
        staff_person = get_person_contact(staff_user)
        response = client.post(
            "/api/shuup/basket/new/", data={"shop": shop.pk, "customer": staff_person.pk})
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
            "/api/shuup/basket/new/", data={"shop": shop.pk, "customer": person.pk})
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
def test_basket_reorder_staff_user():
    with override_settings(**REQUIRED_SETTINGS):
        set_configuration()
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
        response = client.post("/api/shuup/basket/new/", data={"shop": shop.pk, "customer": person.pk}, format="json")
        # Only stuff linked to shop can create baskets for someone else
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Can still add personal baskets
        staff_person = get_person_contact(staff_user)
        response = client.post("/api/shuup/basket/new/", data={"shop": shop.pk, "customer": staff_person.pk}, format="json")
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
        response = client.post("/api/shuup/basket/new/", data={"shop": shop.pk, "customer": person.pk}, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        basket_data = json.loads(response.content.decode("utf-8"))
        basket = Basket.objects.filter(key=basket_data["uuid"].split("-")[1]).first()
        assert basket.shop == shop
        assert basket.creator == staff_user
        assert basket.customer.pk == person.pk
        response = client.get("/api/shuup/basket/{}/".format(basket_data["uuid"]))
        assert response.status_code == 200
        assert basket.creator == staff_user
        assert basket.customer.pk == person.pk

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
        assert created_order.creator == staff_user
        assert created_order.customer == person

        # create a second customer
        person2 = factories.create_random_person()
        # create a basket for customer 2 and try to fill with contents of customer 1 order - it should not be possible
        response = client.post("/api/shuup/basket/new/", data={"shop": shop.pk, "customer": person2.pk}, format="json")
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


def _get_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client
