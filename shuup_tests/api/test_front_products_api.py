# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json
import random
from collections import defaultdict
from decimal import Decimal

import pytest
from rest_framework import status
from rest_framework.test import (
    APIClient, APIRequestFactory, force_authenticate
)

from shuup.core import cache
from shuup.core.models import (
    AnonymousContact, Category, MutableAddress, OrderStatus, Product,
    ProductCrossSell, ProductCrossSellType, ProductMedia, ProductMediaKind,
    ProductVisibility, Shop, ShopProduct, ShopProductVisibility, ShopStatus,
    Supplier
)
from shuup.front.api.products import FrontProductViewSet
from shuup.testing.factories import (
    add_product_to_order, create_empty_order, create_package_product,
    create_product, create_random_contact_group, create_random_order,
    create_random_person, get_default_shop, get_random_filer_image
)


def setup_function(fn):
    cache.clear()


def create_simple_supplier(identifier):
    ident = "supplier_%s" % identifier
    return Supplier.objects.create(
        identifier=ident,
        name=ident,
        module_identifier="simple_supplier",
    )


def get_request(path, user, customer=None, data=None):
    factory = APIRequestFactory()
    request = factory.get(path, data=data)
    force_authenticate(request, user)
    request.customer = customer
    return request


@pytest.mark.django_db
def test_get_products(admin_user):
    shop1 = get_default_shop()

    person1 = create_random_person()
    person1.user = admin_user
    person1.save()

    person2 = create_random_person()
    person2.save()


@pytest.mark.django_db
def test_no_products(admin_user):
    get_default_shop()

    person1 = create_random_person()
    person1.user = admin_user
    person1.save()

    # list all orderable products
    request = get_request("/api/shuup/front/products/", admin_user, person1)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    assert response.status_code == status.HTTP_200_OK
    products_data = json.loads(response.content.decode("utf-8"))
    assert len(products_data) == 0


@pytest.mark.django_db
def test_products_all_shops(admin_user):
    shop1 = get_default_shop()
    shop1.logo = get_random_filer_image()
    shop1.save()

    person1 = create_random_person()
    person1.user = admin_user
    person1.save()

    shop2 = Shop.objects.create()
    shop2.favicon = get_random_filer_image()
    shop2.save()
    supplier1 = create_simple_supplier("supplier1")
    supplier2 = create_simple_supplier("supplier2")

    # create 2 products for shop2
    product1 = create_product("product1", shop=shop1, supplier=supplier1)
    product2 = create_product("product2", shop=shop2, supplier=supplier2)
    product3 = create_product("product3", shop=shop2, supplier=supplier1)

    # list all orderable products - 2 just created are for shop2
    request = get_request("/api/shuup/front/products/", admin_user, person1)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    products = json.loads(response.content.decode("utf-8"))
    assert len(products) == 3

    assert products[0]["product_id"] == product1.id
    assert products[0]["shop"]["id"] == shop1.id
    assert products[0]["shop"]["logo"] == request.build_absolute_uri(shop1.logo.url)

    assert products[1]["product_id"] == product2.id
    assert products[1]["shop"]["id"] == shop2.id
    assert products[1]["shop"]["favicon"] == request.build_absolute_uri(shop2.favicon.url)

    assert products[2]["product_id"] == product3.id
    assert products[2]["shop"]["id"] == shop2.id
    assert products[2]["shop"]["favicon"] == request.build_absolute_uri(shop2.favicon.url)


@pytest.mark.django_db
def test_products_not_available_shop(admin_user):
    shop1 = get_default_shop()
    person1 = create_random_person()
    person1.user = admin_user
    person1.save()

    supplier1 = create_simple_supplier("supplier1")
    product1 = create_product("product1", shop=shop1, supplier=supplier1)
    product3 = create_product("product3", shop=shop1, supplier=supplier1)
    # add images for products 1 and 3
    add_product_image(product1)
    add_product_image(product3)

    # product 3 not visible
    shop1_product3 = ShopProduct.objects.get(shop=shop1, product=product3)
    shop1_product3.visibility = ShopProductVisibility.NOT_VISIBLE
    shop1_product3.save()

    request = get_request("/api/shuup/front/products/", admin_user, person1)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    products_data = json.loads(response.content.decode("utf-8"))
    assert len(products_data) == 1

    # now product3 becomes visible
    shop1_product3.visibility = ShopProductVisibility.ALWAYS_VISIBLE
    shop1_product3.save()
    request = get_request("/api/shuup/front/products/", admin_user, person1)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    products_data = json.loads(response.content.decode("utf-8"))
    assert len(products_data) == 2
    assert products_data[0]["is_orderable"] is True
    assert products_data[1]["is_orderable"] is True

    # check for images
    assert products_data[0]["image"] == request.build_absolute_uri(product1.primary_image.url)
    assert products_data[1]["image"] == request.build_absolute_uri(product3.primary_image.url)


@pytest.mark.django_db
def test_products_name_sort(admin_user):
    shop1 = get_default_shop()
    supplier1 = create_simple_supplier("supplier1")
    product1 = create_product("product1", shop=shop1, supplier=supplier1)
    product2 = create_product("product2", shop=shop1, supplier=supplier1)
    product3 = create_product("product3", shop=shop1, supplier=supplier1)

    # ordering by -name
    request = get_request("/api/shuup/front/products/?sort=-name", admin_user)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    products_data = json.loads(response.content.decode("utf-8"))
    assert products_data[0]["product_id"] == product3.id
    assert products_data[0]["is_orderable"] is True
    assert products_data[1]["product_id"] == product2.id
    assert products_data[1]["is_orderable"] is True
    assert products_data[2]["product_id"] == product1.id
    assert products_data[2]["is_orderable"] is True


@pytest.mark.django_db
def test_products_not_available_shop(admin_user):
    shop1 = get_default_shop()
    supplier1 = create_simple_supplier("supplier1")
    product1 = create_product("product1", shop=shop1, supplier=supplier1)
    product2 = create_product("product2", shop=shop1, supplier=supplier1)

    # add categories to products
    category1 = Category.objects.create(parent=None, identifier="category1", name="category1")
    shop_product1 = ShopProduct.objects.get(shop=shop1, product=product1)
    shop_product1.primary_category = category1
    shop_product1.categories.add(category1)
    shop_product1.save()
    category2 = Category.objects.create(parent=None, identifier="category2", name="category2")
    shop_product2 = ShopProduct.objects.get(shop=shop1, product=product2)
    shop_product2.primary_category = category2
    shop_product2.categories.add(category2)
    shop_product2.save()

    # fetch by category1
    request = get_request("/api/shuup/front/products/?categories=%d" % category1.id, admin_user)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    products_data = json.loads(response.content.decode("utf-8"))
    assert len(products_data) == 1
    assert products_data[0]["product_id"] == product1.id

    # fetch by category2
    request = get_request("/api/shuup/front/products/?categories=%d" % category2.id, admin_user)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    products_data = json.loads(response.content.decode("utf-8"))
    assert len(products_data) == 1
    assert products_data[0]["product_id"] == product2.id

    # fetch by category 1 and 2
    request = get_request("/api/shuup/front/products/?categories=%d,%d" % (category1.id, category2.id), admin_user)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    products_data = json.loads(response.content.decode("utf-8"))
    assert len(products_data) == 2
    assert products_data[0]["product_id"] == product1.id
    assert products_data[1]["product_id"] == product2.id


@pytest.mark.django_db
def test_product_package(admin_user):
    shop1 = get_default_shop()
    supplier1 = create_simple_supplier("supplier1")
    product4 = create_package_product("product4", shop=shop1, supplier=supplier1)

    request = get_request("/api/shuup/front/products/", admin_user)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    products_data = json.loads(response.content.decode("utf-8"))
    products = sorted(products_data, key=lambda p: p["id"])
    assert products[0]["product_id"] == product4.id
    assert products[0]["is_orderable"] is True
    assert len(products[0]["package_content"]) == product4.get_all_package_children().count()


@pytest.mark.django_db
def test_product_cross_sells(admin_user):
    shop1 = get_default_shop()
    supplier1 = create_simple_supplier("supplier1")
    product1 = create_product("product1", shop=shop1, supplier=supplier1)
    product2 = create_product("product2", shop=shop1, supplier=supplier1)

    # assign cross sell of product1 and product2
    ProductCrossSell.objects.create(product1=product1, product2=product2, type=ProductCrossSellType.RECOMMENDED)
    ProductCrossSell.objects.create(product1=product1, product2=product2, type=ProductCrossSellType.RELATED)
    ProductCrossSell.objects.create(product1=product1, product2=product2, type=ProductCrossSellType.COMPUTED)
    ProductCrossSell.objects.create(product1=product1, product2=product2, type=ProductCrossSellType.BOUGHT_WITH)

    # product1 must have cross shell of product2
    request = get_request("/api/shuup/front/products/", admin_user)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    products_data = json.loads(response.content.decode("utf-8"))
    products = sorted(products_data, key=lambda p: p["id"])

    assert products[0]["product_id"] == product1.id
    assert products[0]["cross_sell"]["recommended"][0]["product_id"] == product2.id
    assert products[0]["cross_sell"]["related"][0]["product_id"] == product2.id
    assert products[0]["cross_sell"]["computed"][0]["product_id"] == product2.id
    assert products[0]["cross_sell"]["bought_with"][0]["product_id"] == product2.id

    assert products[1]["product_id"] == product2.id
    assert products[1]["cross_sell"]["recommended"] == []
    assert products[1]["cross_sell"]["related"] == []
    assert products[1]["cross_sell"]["computed"] == []
    assert products[1]["cross_sell"]["bought_with"] == []


@pytest.mark.django_db
def test_get_best_selling_products(admin_user):
    shop1 = get_default_shop()
    person1 = create_random_person()
    person1.user = admin_user
    person1.save()

    supplier = create_simple_supplier("supplier1")
    client = _get_client(admin_user)

    # list best selling products
    response = client.get("/api/shuup/front/products/best_selling/")
    assert response.status_code == status.HTTP_200_OK
    products = json.loads(response.content.decode("utf-8"))
    assert len(products) == 0

    # THIS IS IMPORTANT!
    cache.clear()

    products = [create_product("Standard-%d" % x, supplier=supplier, shop=shop1) for x in range(10)]

    # create 1 product with 4 variations
    parent_product = create_product("ParentProduct1", supplier=supplier, shop=shop1)
    children = [create_product("SimpleVarChild-%d" % x, supplier=supplier, shop=shop1) for x in range(4)]
    for child in children:
        child.link_to_parent(parent_product)

    best_selling = defaultdict(int)

    # create orders with standard products
    for p_index in range(len(products)):
        order = create_empty_order(shop=shop1)
        order.save()
        qty = (len(products)-p_index)
        add_product_to_order(order, supplier, products[p_index], qty, Decimal(1.0))
        order.create_shipment_of_all_products()
        order.status = OrderStatus.objects.get_default_complete()
        order.save(update_fields=("status",))

        best_selling[products[p_index].id] = qty

    # create orders with variation products - the parent product is counted instead of its children
    for p_index in range(2):
        variation = random.choice(children)
        qty = 5
        order = create_empty_order(shop=shop1)
        order.save()
        add_product_to_order(order, supplier, variation, qty, Decimal(1.0))
        order.create_shipment_of_all_products()
        order.status = OrderStatus.objects.get_default_complete()
        order.save(update_fields=("status",))
        best_selling[parent_product.id] = best_selling[parent_product.id] + qty

    # get the top 100 best selling products
    response = client.get("/api/shuup/front/products/best_selling/", {"limit": 100})
    assert response.status_code == status.HTTP_200_OK
    products = json.loads(response.content.decode("utf-8"))
    assert len(products) == len(best_selling) # as we added less then 100, this must be true

    # check the if all IDS are part of best selling
    for ix in range(len(products)):
        assert products[ix]["product_id"] in best_selling.keys()

    # get the top 5 best selling products
    response = client.get("/api/shuup/front/products/best_selling/", {"limit": 5})
    assert response.status_code == status.HTTP_200_OK
    products = json.loads(response.content.decode("utf-8"))
    assert len(products) == 5
    sorted_best_selling_ids = [prod[0] for prod in sorted(best_selling.items(), key=lambda prod: -prod[1])][:5]

    # check the if all the 5 best sellers are part of best selling
    for ix in range(len(products)):
        assert products[ix]["product_id"] in sorted_best_selling_ids


@pytest.mark.django_db
def test_get_newest_products(admin_user):
    shop1 = get_default_shop()
    shop2 = Shop.objects.create()

    customer = create_random_person()
    customer.user = admin_user
    customer.save()

    client = _get_client(admin_user)
    client.customer = customer
    client.shop = shop1

    # list newest products
    response = client.get("/api/shuup/front/products/?sort=newest")
    assert response.status_code == status.HTTP_200_OK
    products = json.loads(response.content.decode("utf-8"))
    assert len(products) == 0

    supplier = create_simple_supplier("supplier1")

    # create 30 random products
    for x in range(30):
        # product for shop1
        p1 = create_product("product-%d-1" % x, shop=shop1, supplier=supplier)
        # product for shop2
        p2 = create_product("product-%d-2" % x, shop=shop2, supplier=supplier)

    # list newest products
    data = {"limit": 100, "sort": "newest", "shops": shop1.id}
    request = get_request("/api/shuup/front/products/", admin_user, customer, data=data)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    assert response.status_code == status.HTTP_200_OK
    products = json.loads(response.content.decode("utf-8"))["results"]

    # only the shop of params must be considered
    newest_products = Product.objects.filter(shop_products__shop=shop1).order_by("-pk")
    assert len(products) == newest_products.count()

    # the result must be a ordered list of products (ordered by newest)
    ids = [p["product_id"] for p in products]
    assert ids == list(newest_products.values_list("pk", flat=True))

    # shop2 - limit the numbers of the result
    data = {"limit": 10, "sort": "newest", "shops": shop2.id}
    request = get_request("/api/shuup/front/products/", admin_user, customer, data)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    assert response.status_code == status.HTTP_200_OK
    products = json.loads(response.content.decode("utf-8"))["results"]
    newest_products = Product.objects.filter(shop_products__shop=shop2).order_by("-created_on")[:10]
    assert len(products) == newest_products.count()
    ids = [p["product_id"] for p in products]
    assert ids == list(newest_products.values_list("pk", flat=True))



@pytest.mark.django_db
def test_nearby_products(admin_user):
    get_default_shop()
    supplier = create_simple_supplier("supplier1")
    client = _get_client(admin_user)

    # create Apple and its products
    shop1 = Shop.objects.create(status=ShopStatus.ENABLED)
    shop1.contact_address = MutableAddress.objects.create(
        name="Apple Infinite Loop",
        street="1 Infinite Loop",
        country="US",
        city="Cupertino",
        latitude=37.331667,
        longitude=-122.030146
    )
    shop1.save()
    product1 = create_product("macbook", shop1, supplier=supplier)
    product2 = create_product("imac", shop1, supplier=supplier)

    # create Google and its products
    shop2 = Shop.objects.create(status=ShopStatus.ENABLED)
    shop2.contact_address = MutableAddress.objects.create(
        name="Google",
        street="1600 Amphitheatre Pkwy",
        country="US",
        city="Mountain View",
        latitude=37.422000,
        longitude=-122.084024
    )
    shop2.save()
    product3 = create_product("nexus 1", shop2, supplier=supplier)
    product4 = create_product("nexux 7", shop2, supplier=supplier)

    my_position_to_apple = 2.982
    my_position_to_google = 10.57
    # YMCA
    my_position = (37.328330, -122.063612)

    # fetch only apple products - max distance = 5km - order by name
    params = {"distance": 5, "lat": my_position[0], "lng": my_position[1], "sort": "name"}
    request = get_request("/api/shuup/front/products/", admin_user, data=params)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    assert response.status_code == status.HTTP_200_OK
    products = json.loads(response.content.decode("utf-8"))
    assert len(products) == 2
    assert products[0]["product_id"] == product2.id
    assert products[0]["name"] == product2.name
    assert products[0]["shop"]["id"] == shop1.id
    assert products[0]["distance"] - my_position_to_apple < 0.05    # 5 meters of error margin

    assert products[1]["product_id"] == product1.id
    assert products[1]["name"] == product1.name
    assert products[1]["shop"]["id"] == shop1.id
    assert products[1]["distance"] - my_position_to_apple < 0.05    # 5 meters of error margin

    # fetch only all products - no max distance - order by distance DESC
    params = {"lat": my_position[0], "lng": my_position[1], "sort": "-distance"}
    request = get_request("/api/shuup/front/products/", admin_user, data=params)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    assert response.status_code == status.HTTP_200_OK
    products = json.loads(response.content.decode("utf-8"))
    assert len(products) == 4

    assert products[0]["product_id"] == product3.id
    assert products[0]["name"] == product3.name
    assert products[0]["shop"]["id"] == shop2.id
    assert products[0]["distance"] - my_position_to_google < 0.05    # 5 meters of error margin

    assert products[1]["product_id"] == product4.id
    assert products[1]["name"] == product4.name
    assert products[1]["shop"]["id"] == shop2.id
    assert products[1]["distance"] - my_position_to_google < 0.05    # 5 meters of error margin

    assert products[2]["product_id"] == product1.id
    assert products[2]["name"] == product1.name
    assert products[2]["shop"]["id"] == shop1.id
    assert products[2]["distance"] - my_position_to_apple < 0.05    # 5 meters of error margin

    assert products[3]["product_id"] == product2.id
    assert products[3]["name"] == product2.name
    assert products[3]["shop"]["id"] == shop1.id
    assert products[3]["distance"] - my_position_to_apple < 0.05    # 5 meters of error margin


def add_product_image(product):
    media1 = ProductMedia.objects.create(product=product,
                                         kind=ProductMediaKind.IMAGE,
                                         file=get_random_filer_image(),
                                         enabled=True,
                                         public=True)
    media2 = ProductMedia.objects.create(product=product,
                                         kind=ProductMediaKind.IMAGE,
                                         file=get_random_filer_image(),
                                         enabled=True,
                                         public=True)
    product.primary_image = media1
    product.media.add(media2)
    product.save()


def _get_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client
