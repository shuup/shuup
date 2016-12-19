# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
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
    AnonymousContact, Category, OrderStatus, Product, ProductCrossSell,
    ProductCrossSellType, ProductMedia, ProductMediaKind, ProductVisibility,
    Shop, ShopProduct, ShopProductVisibility, Supplier
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


def get_request(path, user, shop, customer):
    factory = APIRequestFactory()
    request = factory.get(path)
    force_authenticate(request, user)
    request.customer = customer
    request.shop = shop
    return request


@pytest.mark.django_db
def test_get_products(admin_user):
    shop1 = get_default_shop()

    person1 = create_random_person()
    person1.user = admin_user
    person1.save()

    person2 = create_random_person()
    person2.save()

    client = _get_client(admin_user)
    client.customer = person1
    client.shop = shop1

    # list all orderable products
    request = get_request("/api/shuup/front/products/", admin_user, shop1, person1)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    assert response.status_code == status.HTTP_200_OK
    products_data = json.loads(response.content.decode("utf-8"))
    assert len(products_data) == 0

    shop2 = Shop.objects.create()
    supplier1 = create_simple_supplier("supplier1")
    supplier2 = create_simple_supplier("supplier2")

    # create 2 products for shop2
    product1 = create_product("product1", shop=shop2, supplier=supplier1)
    product2 = create_product("product2", shop=shop2, supplier=supplier2)

    # add images for products 1 and 2
    add_product_image(product1)
    add_product_image(product2)

    # list all orderable products - None, since the 2 just created are for shop2
    request = get_request("/api/shuup/front/products/", admin_user, shop1, person1)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    products_data = json.loads(response.content.decode("utf-8"))
    assert len(products_data) == 0

    # create the product for shop1 but set it as not visible
    product3 = create_product("product3", shop=shop1, supplier=supplier1)
    shop1_product3 = ShopProduct.objects.get(shop=shop1, product=product3)
    shop1_product3.visibility = ShopProductVisibility.NOT_VISIBLE
    shop1_product3.save()

    # list all orderable products - No one yet
    request = get_request("/api/shuup/front/products/", admin_user, shop1, person1)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    products_data = json.loads(response.content.decode("utf-8"))
    assert len(products_data) == 0

    # now product3 becomes visible
    shop1_product3.visibility = ShopProductVisibility.ALWAYS_VISIBLE
    shop1_product3.save()
    request = get_request("/api/shuup/front/products/", admin_user, shop1, person1)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    products_data = json.loads(response.content.decode("utf-8"))
    assert len(products_data) == 1
    assert products_data[0]["shop_products"][0]["orderable"] is True

    # product should be visible only for some groups
    group = create_random_contact_group()
    group.members.add(person2)
    product3.visibility = ProductVisibility.VISIBLE_TO_GROUPS
    product3.save()
    shop1_product3.visibility_limit = ProductVisibility.VISIBLE_TO_GROUPS
    shop1_product3.visibility_groups.add(group)
    shop1_product3.save()

    request = get_request("/api/shuup/front/products/", admin_user, shop1, person1)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    products_data = json.loads(response.content.decode("utf-8"))
    assert len(products_data) == 0

    # visible for person2 which is in the same group
    request = get_request("/api/shuup/front/products/", admin_user, shop1, person2)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    products_data = json.loads(response.content.decode("utf-8"))
    assert len(products_data) == 1

    # product1 and product2 are visible in shop2
    request = get_request("/api/shuup/front/products/", admin_user, shop2, person1)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    products_data = json.loads(response.content.decode("utf-8"))
    products = sorted(products_data, key=lambda p: p["id"])
    assert products[0]["id"] == product1.id
    assert products[0]["shop_products"][0]["orderable"] is True
    assert products[1]["id"] == product2.id
    assert products[1]["shop_products"][0]["orderable"] is True

    # check for medias
    assert products[0]["primary_image"]["url"] == request.build_absolute_uri(product1.primary_image.url)
    assert products[0]["media"][0]["url"] == request.build_absolute_uri(product1.media.first().url)
    assert products[0]["media"][1]["url"] == request.build_absolute_uri(product1.media.all()[1].url)

    assert products[1]["primary_image"]["url"] == request.build_absolute_uri(product2.primary_image.url)
    assert products[1]["media"][0]["url"] == request.build_absolute_uri(product2.media.first().url)
    assert products[1]["media"][1]["url"] == request.build_absolute_uri(product2.media.all()[1].url)

    # ordering by -id
    request = get_request("/api/shuup/front/products/?ordering=-id", admin_user, shop2, person1)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    products_data = json.loads(response.content.decode("utf-8"))
    assert products_data[0]["id"] == product2.id
    assert products_data[0]["shop_products"][0]["orderable"] is True
    assert products_data[1]["id"] == product1.id
    assert products_data[1]["shop_products"][0]["orderable"] is True

    # add categories to products
    category1 = Category.objects.create(parent=None, identifier="category1", name="category1")
    shop2_product1 = ShopProduct.objects.get(shop=shop2, product=product1)
    shop2_product1.primary_category = category1
    shop2_product1.categories.add(category1)
    shop2_product1.save()
    category2 = Category.objects.create(parent=None, identifier="category2", name="category2")
    shop2_product2 = ShopProduct.objects.get(shop=shop2, product=product2)
    shop2_product2.primary_category = category2
    shop2_product2.categories.add(category2)
    shop2_product2.save()

    # fetch by category1
    request = get_request("/api/shuup/front/products/?category=%d" % category1.id, admin_user, shop2, person1)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    products_data = json.loads(response.content.decode("utf-8"))
    assert len(products_data) == 1
    assert products_data[0]["id"] == product1.id

    # fetch by category2
    request = get_request("/api/shuup/front/products/?category=%d" % category2.id, admin_user, shop2, person1)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    products_data = json.loads(response.content.decode("utf-8"))
    assert len(products_data) == 1
    assert products_data[0]["id"] == product2.id

    # create a package product
    product4 = create_package_product("product4", shop=shop1, supplier=supplier1)

    # make product3 orderable again
    product3.visibility = ProductVisibility.VISIBLE_TO_ALL
    product3.save()
    shop1_product3.visibility_limit = ProductVisibility.VISIBLE_TO_ALL
    shop1_product3.visibility_groups.all().delete()
    shop1_product3.save()

    # product3 and product4 are visible in shop1
    request = get_request("/api/shuup/front/products/", admin_user, shop1, person1)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    products_data = json.loads(response.content.decode("utf-8"))
    products = sorted(products_data, key=lambda p: p["id"])
    assert products[0]["id"] == product3.id
    assert products[0]["shop_products"][0]["orderable"] is True
    assert products[1]["id"] == product4.id
    assert products[1]["shop_products"][0]["orderable"] is True

    # change the shop of the first child product to make the package not orderable
    sp = product4.get_all_package_children()[0].shop_products.first()
    sp.shop = shop2
    sp.save()

    # product3 is orderable and product4 doesn't
    request = get_request("/api/shuup/front/products/", admin_user, shop1, person1)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    products_data = json.loads(response.content.decode("utf-8"))
    products = sorted(products_data, key=lambda p: p["id"])
    assert products[0]["id"] == product3.id
    assert products[0]["shop_products"][0]["orderable"] is True
    assert products[1]["id"] == product4.id
    assert products[1]["shop_products"][0]["orderable"] is False

    # assign cross sell of product1 and product2
    ProductCrossSell.objects.create(product1=product1, product2=product2, type=ProductCrossSellType.RECOMMENDED)
    ProductCrossSell.objects.create(product1=product1, product2=product2, type=ProductCrossSellType.RELATED)
    ProductCrossSell.objects.create(product1=product1, product2=product2, type=ProductCrossSellType.COMPUTED)
    ProductCrossSell.objects.create(product1=product1, product2=product2, type=ProductCrossSellType.BOUGHT_WITH)

    # product1 must have cross shell of product2
    request = get_request("/api/shuup/front/products/", admin_user, shop2, person1)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    products_data = json.loads(response.content.decode("utf-8"))
    products = sorted(products_data, key=lambda p: p["id"])

    assert products[0]["id"] == product1.id
    assert products[0]["cross_sell"]["recommended"] == [product2.id]
    assert products[0]["cross_sell"]["related"] == [product2.id]
    assert products[0]["cross_sell"]["computed"] == [product2.id]
    assert products[0]["cross_sell"]["bought_with"] == [product2.id]

    assert products[1]["id"] == product2.id
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
    response = client.get("/api/shuup/front/products/best_selling/?count=100")
    assert response.status_code == status.HTTP_200_OK
    products = json.loads(response.content.decode("utf-8"))
    assert len(products) == len(best_selling) # as we added less then 100, this must be true

    # check the if all IDS are part of best selling
    for ix in range(len(products)):
        assert products[ix]["id"] in best_selling.keys()

    # get the top 5 best selling products
    response = client.get("/api/shuup/front/products/best_selling/?count=5")
    assert response.status_code == status.HTTP_200_OK
    products = json.loads(response.content.decode("utf-8"))
    assert len(products) == 5
    sorted_best_selling_ids = [prod[0] for prod in sorted(best_selling.items(), key=lambda prod: -prod[1])][:5]

    # check the if all the 5 best sellers are part of best selling
    for ix in range(len(products)):
        assert products[ix]["id"] in sorted_best_selling_ids


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
    response = client.get("/api/shuup/front/products/newest/")
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
    request = get_request("/api/shuup/front/products/newest/?count=100", admin_user, shop1, customer)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    assert response.status_code == status.HTTP_200_OK
    products = json.loads(response.content.decode("utf-8"))

    # only the shop of request must be considered
    newest_products = Product.objects.filter(shop_products__shop=shop1).order_by("-pk")
    assert len(products) == newest_products.count()

    # the result must be a ordered list of products (ordered by newest)
    ids = [p["id"] for p in products]
    assert ids == list(newest_products.values_list("pk", flat=True))

    # shop2 - limit the numbers of the result
    request = get_request("/api/shuup/front/products/newest/?count=10", admin_user, shop2, customer)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    assert response.status_code == status.HTTP_200_OK
    products = json.loads(response.content.decode("utf-8"))
    newest_products = Product.objects.filter(shop_products__shop=shop2).order_by("-pk")
    assert len(products) == newest_products.count()
    ids = [p["id"] for p in products]
    assert ids == list(newest_products.values_list("pk", flat=True))


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
