# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json
import random
from collections import defaultdict
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils.translation import activate
from rest_framework import status
from rest_framework.test import (
    APIClient, APIRequestFactory, force_authenticate
)

from shuup import configuration
from shuup.core import cache
from shuup.core.api.front_products import (
    FrontProductViewSet, FrontShopProductViewSet
)
from shuup.core.models import (
    Category, get_person_contact, MutableAddress, OrderStatus, Product,
    ProductCrossSell, ProductCrossSellType, ProductMedia, ProductMediaKind,
    ProductMode, ProductVariationVariable, ProductVariationVariableValue,
    ProductVisibility, Shop, ShopProduct, ShopProductVisibility, ShopStatus,
    Supplier
)
from shuup.utils.money import Money
from shuup.customer_group_pricing.models import CgpDiscount, CgpPrice
from shuup.testing import factories
from shuup.testing.factories import (
    add_product_to_order, create_empty_order, create_package_product,
    create_product, create_random_contact_group, create_random_person,
    get_default_shop, get_default_supplier, get_random_filer_image, get_shop
)


def setup_function(fn):
    activate("en")
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
    shop = get_default_shop()
    supplier = get_default_supplier()

    person1 = create_random_person()
    person1.user = admin_user
    person1.save()

    create_product("product1", shop=shop, supplier=supplier)
    create_product("product2", shop=shop, supplier=supplier)

    # Generate complex variations
    product_parent = create_product("product3", shop=shop, supplier=supplier)
    populate_variations_for_parent(product_parent, shop, supplier)
    assert product_parent.mode == ProductMode.VARIABLE_VARIATION_PARENT

    # Generate simple variations
    simple_parent = create_product("product4", shop=shop, supplier=supplier)
    simple_child = create_product("product5", shop=shop, supplier=supplier)
    simple_child.link_to_parent(simple_parent)
    assert simple_child.is_variation_child()
    assert simple_parent.mode == ProductMode.SIMPLE_VARIATION_PARENT

    request = get_request("/api/shuup/front/shop_products/", admin_user, person1)
    response = FrontShopProductViewSet.as_view({"get": "list"})(request)
    response.render()
    assert response.status_code == status.HTTP_200_OK
    products_data = json.loads(response.content.decode("utf-8"))
    assert len(products_data) == 4

    complex_parent_data = [data for data in products_data if data["product_id"] == product_parent.id][0]
    assert len(complex_parent_data["variations"]) == 12

    simple_parent_data = [data for data in products_data if data["product_id"] == simple_parent.id][0]
    assert len(simple_parent_data["variations"]) == 1
    assert simple_parent_data["variations"][0]["sku_part"] == simple_child.sku
    assert simple_parent_data["variations"][0]["product"]["product_id"] == simple_child.id


def populate_variations_for_parent(parent, shop, supplier):
    color_var = ProductVariationVariable.objects.create(product=parent, identifier="color")
    size_var = ProductVariationVariable.objects.create(product=parent, identifier="size")

    for color in ("yellow", "blue", "brown"):
        ProductVariationVariableValue.objects.create(variable=color_var, identifier=color)

    for size in ("small", "medium", "large", "huge"):
        ProductVariationVariableValue.objects.create(variable=size_var, identifier=size)

    combinations = list(parent.get_all_available_combinations())
    assert len(combinations) == (3 * 4)
    for combo in combinations:
        assert not combo["result_product_pk"]
        child = create_product("xyz-%s" % combo["sku_part"], shop=shop, supplier=supplier)
        child.link_to_parent(parent, combo["variable_to_value"])


@pytest.mark.django_db
def test_no_products(admin_user):
    get_default_shop()

    person1 = create_random_person()
    person1.user = admin_user
    person1.save()

    # list all orderable products
    request = get_request("/api/shuup/front/shop_products/", admin_user, person1)
    response = FrontShopProductViewSet.as_view({"get": "list"})(request)
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

    shop2 = Shop.objects.create(status=ShopStatus.ENABLED)
    shop2.favicon = get_random_filer_image()
    shop2.save()
    supplier1 = create_simple_supplier("supplier1")
    supplier2 = create_simple_supplier("supplier2")

    # create 2 products for shop2
    product1 = create_product("product1", shop=shop1, supplier=supplier1)
    product2 = create_product("product2", shop=shop2, supplier=supplier2)
    product3 = create_product("product3", shop=shop2, supplier=supplier1)

    # list all orderable products - 2 just created are for shop2
    request = get_request("/api/shuup/front/shop_products/", admin_user, person1)
    response = FrontShopProductViewSet.as_view({"get": "list"})(request)
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

    request = get_request("/api/shuup/front/shop_products/", admin_user, person1)
    response = FrontShopProductViewSet.as_view({"get": "list"})(request)
    response.render()
    products_data = json.loads(response.content.decode("utf-8"))
    assert len(products_data) == 1

    # now product3 becomes visible
    shop1_product3.visibility = ShopProductVisibility.ALWAYS_VISIBLE
    shop1_product3.save()
    request = get_request("/api/shuup/front/shop_products/", admin_user, person1)
    response = FrontShopProductViewSet.as_view({"get": "list"})(request)
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
    request = get_request("/api/shuup/front/shop_products/?ordering=-name", admin_user)
    response = FrontShopProductViewSet.as_view({"get": "list"})(request)
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
    request = get_request("/api/shuup/front/shop_products/?categories=%d" % category1.id, admin_user)
    response = FrontShopProductViewSet.as_view({"get": "list"})(request)
    response.render()
    products_data = json.loads(response.content.decode("utf-8"))
    assert len(products_data) == 1
    assert products_data[0]["product_id"] == product1.id

    # fetch by category2
    request = get_request("/api/shuup/front/shop_products/?categories=%d" % category2.id, admin_user)
    response = FrontShopProductViewSet.as_view({"get": "list"})(request)
    response.render()
    products_data = json.loads(response.content.decode("utf-8"))
    assert len(products_data) == 1
    assert products_data[0]["product_id"] == product2.id

    # fetch by category 1 and 2
    request = get_request("/api/shuup/front/shop_products/?categories=%d,%d" % (category1.id, category2.id), admin_user)
    response = FrontShopProductViewSet.as_view({"get": "list"})(request)
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

    request = get_request("/api/shuup/front/shop_products/", admin_user)
    response = FrontShopProductViewSet.as_view({"get": "list"})(request)
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
    request = get_request("/api/shuup/front/shop_products/", admin_user)
    response = FrontShopProductViewSet.as_view({"get": "list"})(request)
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
    shop2 = get_shop(True)
    person1 = create_random_person()
    person1.user = admin_user
    person1.save()

    supplier = create_simple_supplier("supplier1")
    client = _get_client(admin_user)

    # list best selling products
    response = client.get("/api/shuup/front/shop_products/best_selling/", {"shop": shop2.pk, "limit": 20})
    assert response.status_code == status.HTTP_200_OK
    products = json.loads(response.content.decode("utf-8"))
    assert len(products["results"]) == 0

    # THIS IS IMPORTANT!
    cache.clear()

    products = [create_product("Standard-%d" % x, supplier=supplier, shop=shop2) for x in range(10)]

    # create 1 product with 4 variations
    parent_product = create_product("ParentProduct1", supplier=supplier, shop=shop2)
    children = [create_product("SimpleVarChild-%d" % x, supplier=supplier, shop=shop2) for x in range(4)]
    for child in children:
        child.link_to_parent(parent_product)

    best_selling = defaultdict(int)

    # create orders with standard products
    for p_index in range(len(products)):
        order = create_empty_order(shop=shop2)
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
        order = create_empty_order(shop=shop2)
        order.save()
        add_product_to_order(order, supplier, variation, qty, Decimal(1.0))
        order.create_shipment_of_all_products()
        order.status = OrderStatus.objects.get_default_complete()
        order.save(update_fields=("status",))
        best_selling[parent_product.id] = best_selling[parent_product.id] + qty

    # get the top 100 best selling products
    response = client.get("/api/shuup/front/shop_products/best_selling/", {"shop": shop2.pk, "limit": 100})
    assert response.status_code == status.HTTP_200_OK
    products = json.loads(response.content.decode("utf-8"))
    assert len(products["results"]) == len(best_selling) # as we added less then 100, this must be true
    assert products["next"] is None

    # check the if all IDS are part of best selling
    for ix in range(len(products)):
        assert products["results"][ix]["product_id"] in best_selling.keys()

    # get the top 5 best selling products (we should get paginated results)
    response = client.get("/api/shuup/front/shop_products/best_selling/", {"shop": shop2.pk, "limit": 5})
    assert response.status_code == status.HTTP_200_OK
    products = json.loads(response.content.decode("utf-8"))
    assert len(products["results"]) == 5
    assert products["count"] == len(best_selling)
    assert products["next"] is not None
    sorted_best_selling_ids = [prod[0] for prod in sorted(best_selling.items(), key=lambda prod: -prod[1])][:5]

    # check the if all the 5 best sellers are part of best selling
    for ix in range(len(products)):
        assert products["results"][ix]["product_id"] in sorted_best_selling_ids


@pytest.mark.django_db
def test_get_newest_products(admin_user):
    shop1 = get_default_shop()
    shop2 = Shop.objects.create(status=ShopStatus.ENABLED)

    customer = create_random_person()
    customer.user = admin_user
    customer.save()

    client = _get_client(admin_user)
    client.customer = customer
    client.shop = shop1

    # list newest products
    response = client.get("/api/shuup/front/shop_products/?ordering=newest")
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
    data = {"limit": 100, "ordering": "newest", "shops": shop1.id}
    request = get_request("/api/shuup/front/shop_products/", admin_user, customer, data=data)
    response = FrontShopProductViewSet.as_view({"get": "list"})(request)
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
    data = {"limit": 10, "ordering": "newest", "shops": shop2.id}
    request = get_request("/api/shuup/front/shop_products/", admin_user, customer, data)
    response = FrontShopProductViewSet.as_view({"get": "list"})(request)
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

    # fetch products and their closest shops
    params = {"lat": my_position[0], "lng": my_position[1], "ordering": "-distance"}
    request = get_request("/api/shuup/front/products/", admin_user, data=params)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    assert response.status_code == status.HTTP_200_OK
    products = json.loads(response.content.decode("utf-8"))
    assert len(products) == 4

    assert products[0]["id"] == product3.id
    assert products[0]["name"] == product3.name
    assert products[0]["closest_shop_distance"] - my_position_to_google < 0.05    # 5 meters of error margin

    assert products[1]["id"] == product4.id
    assert products[1]["name"] == product4.name
    assert products[1]["closest_shop_distance"] - my_position_to_google < 0.05    # 5 meters of error margin

    assert products[2]["id"] == product1.id
    assert products[2]["name"] == product1.name
    assert products[2]["closest_shop_distance"] - my_position_to_apple < 0.05    # 5 meters of error margin

    assert products[3]["id"] == product2.id
    assert products[3]["name"] == product2.name
    assert products[3]["closest_shop_distance"] - my_position_to_apple < 0.05    # 5 meters of error margin


@pytest.mark.django_db
def test_get_front_products(admin_user):
    shop1 = get_default_shop()
    shop2 = Shop.objects.create(status=ShopStatus.ENABLED)
    supplier = get_default_supplier()

    p1 = create_product("product1", shop=shop1, supplier=supplier)
    p2 = create_product("product2", shop=shop1, supplier=supplier)

    sp1 = ShopProduct.objects.get(shop=shop1, product=p1)
    sp2 = ShopProduct.objects.get(shop=shop1, product=p2)

    # add products to other shop
    sp3 = ShopProduct.objects.create(shop=shop2, product=p1)
    sp4 = ShopProduct.objects.create(shop=shop2, product=p2)

    request = get_request("/api/shuup/front/products/", admin_user)
    response = FrontProductViewSet.as_view({"get": "list"})(request)
    response.render()
    assert response.status_code == status.HTTP_200_OK
    products_data = json.loads(response.content.decode("utf-8"))
    # should return only 2 procuts with 2 shops each
    assert len(products_data) == 2
    products = sorted(products_data, key=lambda p: p["id"])
    assert products[0]["id"] == p1.id
    assert products[0]["shop_products"] == [sp1.id, sp3.id]
    assert products[1]["id"] == p2.id
    assert products[1]["shop_products"] == [sp2.id, sp4.id]


@pytest.mark.django_db
def test_get_shop_product_fields(admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()

    shop_product_name = "SHOP Product Name"
    shop_product_description = "SHOP Product Description"
    shop_product_short_description = "SHOP Product Short Description"

    product = create_product("product1", shop=shop, supplier=supplier)
    product.name = "Product Name"
    product.description = "Product Description"
    product.short_description = "Product Short Description"
    product.save()

    shop_product = product.shop_products.first()
    shop_product.name = shop_product_name
    shop_product.description = shop_product_description
    shop_product.short_description = shop_product_short_description
    shop_product.save()

    request = get_request("/api/shuup/front/shop_products/", admin_user)
    response = FrontShopProductViewSet.as_view({"get": "list"})(request)
    response.render()
    assert response.status_code == status.HTTP_200_OK
    products_data = json.loads(response.content.decode("utf-8"))
    assert len(products_data) == 1

    product_info = products_data[0]
    assert product_info["name"] == shop_product_name
    assert product_info["description"] == shop_product_description
    assert product_info["short_description"] == shop_product_short_description


@pytest.mark.django_db
def test_product_pricing_cache(admin_user):
    shop = get_default_shop()
    group = create_random_contact_group()
    group2 = create_random_contact_group()
    product = create_product("Just-A-Product", shop, default_price=200)
    CgpPrice.objects.create(product=product, shop=shop, group=group, price_value=175)
    CgpPrice.objects.create(product=product, shop=shop, group=group2, price_value=150)
    client = _get_client(admin_user)
    response = client.get("/api/shuup/front/shop_products/")
    products_data = json.loads(response.content.decode("utf-8"))
    assert products_data[0]["price"] == 200

    user = get_user_model().objects.first()
    user.pk = None
    user.username = "g1"
    user.save()
    customer = create_random_person()
    customer.groups.add(group)
    customer.user = user
    customer.save()
    client = _get_client(user)
    response = client.get("/api/shuup/front/shop_products/")
    products_data = json.loads(response.content.decode("utf-8"))
    assert products_data[0]["price"] == 175

    client = _get_client(admin_user)
    response = client.get("/api/shuup/front/shop_products/")
    products_data = json.loads(response.content.decode("utf-8"))
    assert products_data[0]["price"] == 200


@pytest.mark.django_db
def test_product_variations_cache(admin_user):
    configuration.set(None, "api_permission_FrontShopProductViewSet", 2)
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product("Just-A-Product", shop, default_price=200, supplier=supplier)
    simple_child = create_product("product5", shop=shop, supplier=supplier)
    simple_child.link_to_parent(product)
    sp = simple_child.get_shop_instance(shop)
    sp.visibility_limit = ProductVisibility.VISIBLE_TO_LOGGED_IN
    sp.save()

    client = _get_client(None)
    response = client.get("/api/shuup/front/shop_products/")
    products_data = json.loads(response.content.decode("utf-8"))
    assert not products_data[0]["variations"][0]["product"]["is_orderable"]

    client = _get_client(admin_user)
    response = client.get("/api/shuup/front/shop_products/")
    products_data = json.loads(response.content.decode("utf-8"))
    assert products_data[0]["variations"][0]["product"]["is_orderable"]


def add_product_image(product, purchased=False):
    media1 = ProductMedia.objects.create(
        product=product,
        kind=ProductMediaKind.IMAGE,
        file=get_random_filer_image(),
        enabled=True,
        public=True,
        purchased=purchased
    )
    media2 = ProductMedia.objects.create(
        product=product,
        kind=ProductMediaKind.IMAGE,
        file=get_random_filer_image(),
        enabled=True,
        public=True,
        purchased=purchased
    )
    product.primary_image = media1
    product.media.add(media2)
    product.save()
    return (media1, media2)


@pytest.mark.parametrize("prices_include_tax, product_price, discount, tax_rate, taxful_price, taxless_price", [
    (True, 200.0, 15.0, 0.1, 185.0, 168.18),
    (False, 200.0, 15.0, 0.1, 203.5, 185.0)
])
@pytest.mark.django_db
def test_product_price_info(admin_user, prices_include_tax, product_price, discount, tax_rate, taxful_price, taxless_price):
    shop = get_default_shop()
    shop.prices_include_tax = prices_include_tax
    shop.save()

    customer = create_random_person()
    group = customer.get_default_group()
    customer.user = admin_user
    customer.groups.add(group)
    customer.save()

    tax = factories.get_default_tax()
    tax.rate = Decimal(tax_rate)
    tax.save()

    product = create_product("Just-A-Product", shop, default_price=product_price)
    CgpDiscount.objects.create(product=product, shop=shop, group=group, discount_amount_value=discount)

    client = _get_client(admin_user)
    response = client.get("/api/shuup/front/shop_products/", format="json")
    data = response.data[0]

    discounted_price = (product_price - discount)
    price = (discounted_price if prices_include_tax else discounted_price * (1 + tax_rate))
    base_price = (product_price if prices_include_tax else (product_price * (1 + tax_rate)))
    discount_value = (discount if prices_include_tax else (discount * (1 + tax_rate)))

    price_info = data["price_info"]

    def money_round(value):
        return Money(value, shop.currency).as_rounded(2)

    assert money_round(data["price"]) == money_round(price)
    assert money_round(price_info['base_price']) == money_round(base_price)
    assert money_round(price_info['taxful_price']) == money_round(taxful_price)

    if prices_include_tax:
        assert 'taxless_price' not in price_info
        assert 'taxless_base_price' not in price_info
        assert 'tax_amount' not in price_info
    else:
        assert money_round(price_info['taxless_base_price']) == money_round(product_price)
        assert money_round(price_info['taxful_base_price']) == money_round(base_price)
        assert money_round(price_info['taxless_price']) == money_round(taxless_price)
        assert money_round(price_info['tax_amount']) == money_round((product_price - discount) * tax_rate)

    assert money_round(price_info['price']) == money_round(price)
    assert money_round(price_info['discount_amount']) == money_round(discount_value)
    assert money_round(price_info['discount_rate']) == money_round(discount_value / price if discount else 0)
    assert price_info['is_discounted'] is (True if discount else False)


@pytest.mark.django_db
def test_products_shop_disabled(admin_user):
    shop1 = get_default_shop()
    shop2 = Shop.objects.create(status=ShopStatus.DISABLED)
    supplier1 = create_simple_supplier("supplier1")
    create_product("product1", shop=shop1, supplier=supplier1)
    create_product("product2", shop=shop2, supplier=supplier1)

    request = get_request("/api/shuup/front/shop_products/", admin_user)
    response = FrontShopProductViewSet.as_view({"get": "list"})(request)
    response.render()
    products_data = json.loads(response.content.decode("utf-8"))
    assert len(products_data) == 1


def _get_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client
