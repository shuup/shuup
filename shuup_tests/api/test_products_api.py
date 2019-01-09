# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import base64
import datetime
import json
import os
from decimal import Decimal

from django.utils.timezone import datetime as dt
from django.utils.translation import activate
from rest_framework import status
from rest_framework.test import APIClient

from shuup.core import cache
from shuup.core.models import (
    Attribute, AttributeType, AttributeVisibility, Category, CategoryStatus,
    CategoryVisibility, Manufacturer, Product, ProductAttribute,
    ProductMediaKind, ProductMode, ProductPackageLink, ProductType,
    ProductVisibility, SalesUnit, ShippingMode, Shop, ShopProduct,
    ShopProductVisibility, StockBehavior, Supplier, TaxClass
)
from shuup.testing.factories import (
    ATTR_SPECS, CategoryFactory, create_product, create_random_contact_group,
    create_random_product_attribute, get_default_category,
    get_default_product_type, get_default_sales_unit, get_default_shop,
    get_default_supplier, get_default_tax_class, get_random_filer_image
)


def setup_function(fn):
    cache.clear()


def get_products_by_id_sku(admin_user):
    client = _get_client(admin_user)
    get_default_shop()
    products = [create_product("product 1"), create_product("product 2"), create_product("product 3")]
    client = _get_client(admin_user)

    # get by ID
    response = client.get("/api/shuup/product/?id=%d" % products[2].id)
    assert response.status_code == status.HTTP_200_OK
    product_data = json.loads(response.content.decode("utf-8"))
    assert len(product_data) == 1
    assert product_data[0]["product"] == products[2].id
    assert product_data[0]["sku"] == products[2].id

    # get by SKU
    response = client.get("/api/shuup/product/?sku=%s" % products[1].sku)
    assert response.status_code == status.HTTP_200_OK
    product_data = json.loads(response.content.decode("utf-8"))
    assert len(product_data) == 1
    assert product_data[0]["product"] == products[1].id
    assert product_data[0]["sku"] == products[1].id


def create_simple_supplier(identifier):
    ident = "supplier_%s" % identifier
    return Supplier.objects.create(
        identifier=ident,
        name=ident,
        module_identifier="simple_supplier",
    )


def test_get_product_stocks(admin_user):
    client = _get_client(admin_user)
    shop1 = Shop.objects.create()
    shop2 = Shop.objects.create()

    supplier1 = create_simple_supplier("1")
    supplier2 = create_simple_supplier("2")

    product1 = create_product("product 1")
    product1.stock_behavior = StockBehavior.STOCKED
    product1.save()
    sp = ShopProduct.objects.create(product=product1, shop=shop1)
    sp.suppliers.add(supplier1)
    sp.suppliers.add(supplier2)
    sp = ShopProduct.objects.create(product=product1, shop=shop2)
    sp.suppliers.add(supplier1)
    sp.suppliers.add(supplier2)

    product2 = create_product("product 2")
    product2.stock_behavior = StockBehavior.STOCKED
    product2.save()
    sp = ShopProduct.objects.create(product=product2, shop=shop1)
    sp.suppliers.add(supplier1)
    sp = ShopProduct.objects.create(product=product2, shop=shop2)
    sp.suppliers.add(supplier1)

    product3 = create_product("product 3", shop=shop1, supplier=supplier2)
    product3.stock_behavior = StockBehavior.STOCKED
    product3.save()

    # put some stock
    supplier1.adjust_stock(product1.pk, 100)
    supplier1.adjust_stock(product2.pk, 300)
    supplier2.adjust_stock(product1.pk, 110)
    supplier2.adjust_stock(product3.pk, 300)

    # list all stocks
    response = client.get("/api/shuup/product/stocks/")
    assert response.status_code == status.HTTP_200_OK
    stock_data = sorted(json.loads(response.content.decode("utf-8")),
                        key=lambda prod: prod["product"])
    assert len(stock_data) == 3

    assert stock_data[0]["product"] == product1.pk
    assert stock_data[0]["sku"] == product1.sku
    stocks = sorted(stock_data[0]["stocks"], key=lambda stock: stock["id"])
    assert len(stocks) == 2
    assert stocks[0]["id"] == supplier1.id
    assert stocks[0]["physical_count"] == supplier1.get_stock_status(product1.pk).physical_count
    assert stocks[0]["logical_count"] == supplier1.get_stock_status(product1.pk).logical_count
    assert stocks[1]["id"] == supplier2.id
    assert stocks[1]["physical_count"] == supplier2.get_stock_status(product1.pk).physical_count
    assert stocks[1]["logical_count"] == supplier2.get_stock_status(product1.pk).logical_count

    assert stock_data[1]["product"] == product2.pk
    assert stock_data[1]["sku"] == product2.sku
    stocks = sorted(stock_data[1]["stocks"], key=lambda stock: stock["id"])
    assert len(stocks) == 1
    assert stocks[0]["id"] == supplier1.id
    assert stocks[0]["physical_count"] == supplier1.get_stock_status(product2.pk).physical_count
    assert stocks[0]["logical_count"] == supplier1.get_stock_status(product2.pk).logical_count

    assert stock_data[2]["product"] == product3.pk
    assert stock_data[2]["sku"] == product3.sku
    stocks = sorted(stock_data[2]["stocks"], key=lambda stock: stock["id"])
    assert len(stocks) == 1
    assert stocks[0]["id"] == supplier2.id
    assert stocks[0]["physical_count"] == supplier2.get_stock_status(product3.pk).physical_count
    assert stocks[0]["logical_count"] == supplier2.get_stock_status(product3.pk).logical_count

    # list all stocks - filter by supplier and sku
    response = client.get("/api/shuup/product/stocks/?sku=%s&supplier=%d" % (product1.sku, supplier1.id))
    assert response.status_code == status.HTTP_200_OK
    stock_data = sorted(json.loads(response.content.decode("utf-8")),
                        key=lambda prod: prod["product"])
    assert len(stock_data) == 1
    assert stock_data[0]["product"] == product1.pk
    assert stock_data[0]["sku"] == product1.sku
    assert stock_data[0]["stocks"][0]["id"] == supplier1.id
    assert stock_data[0]["stocks"][0]["physical_count"] == supplier1.get_stock_status(product1.pk).physical_count
    assert stock_data[0]["stocks"][0]["logical_count"] == supplier1.get_stock_status(product1.pk).logical_count

    # list all stocks - filter by supplier and id
    response = client.get("/api/shuup/product/stocks/?product=%d&supplier=%d" % (product2.id, supplier1.id))
    assert response.status_code == status.HTTP_200_OK
    stock_data = sorted(json.loads(response.content.decode("utf-8")),
                        key=lambda prod: prod["product"])
    assert len(stock_data) == 1
    assert stock_data[0]["product"] == product2.pk
    assert stock_data[0]["sku"] == product2.sku
    assert stock_data[0]["stocks"][0]["id"] == supplier1.id
    assert stock_data[0]["stocks"][0]["physical_count"] == supplier1.get_stock_status(product2.pk).physical_count
    assert stock_data[0]["stocks"][0]["logical_count"] == supplier1.get_stock_status(product2.pk).logical_count


def test_create_product(admin_user):
    get_default_shop()
    client = _get_client(admin_user)

    assert Product.objects.count() == 0
    data = _get_product_sample_data()
    response = client.post("/api/shuup/product/", content_type="application/json", data=json.dumps(data))
    assert response.status_code == status.HTTP_201_CREATED

    # check all
    for lang in ("en", "pt-br"):
        activate(lang)
        product = Product.objects.first()
        _check_product_basic_data(product, data, lang)


def test_create_product_with_shop_product(admin_user):
    shop = get_default_shop()
    client = _get_client(admin_user)
    supplier = get_default_supplier()

    cat = Category.objects.create(
        status=CategoryStatus.VISIBLE,
        visibility=CategoryVisibility.VISIBLE_TO_ALL,
        identifier="test_category",
        name="Test"
    )

    assert Product.objects.count() == 0
    data = _get_product_sample_data()
    data["shop_products"] = _get_sample_shop_product_data(shop, cat, supplier)

    response = client.post("/api/shuup/product/", content_type="application/json", data=json.dumps(data))
    assert response.status_code == status.HTTP_201_CREATED

    # check all
    for lang in ("en", "pt-br"):
        activate(lang)
        product = Product.objects.first()
        _check_product_basic_data(product, data, lang)

    assert Product.objects.count() == 1
    assert ShopProduct.objects.count() == 1

    product = Product.objects.first()
    shop_product = ShopProduct.objects.first()

    assert product.get_shop_instance(shop) == shop_product
    assert supplier in shop_product.suppliers.all()
    assert cat in shop_product.categories.all()
    assert shop_product.primary_category == cat


def test_create_product_with_shop_product_and_attributes(admin_user):
    shop = get_default_shop()
    client = _get_client(admin_user)
    supplier = get_default_supplier()

    cat = Category.objects.create(
        status=CategoryStatus.VISIBLE,
        visibility=CategoryVisibility.VISIBLE_TO_ALL,
        identifier="test_category",
        name="Test"
    )
    product_type = get_default_product_type()

    assert Attribute.objects.count() > 0

    assert Product.objects.count() == 0

    attributes_data = []

    expected_values = {
        "untranslated_string_value": "test value",
        "numeric_value": 12,
        "boolean_value": True,
        "timedelta_value": "200",  # seconds
        "datetime_value": "2017-01-01 01:00:00",
        "translated_string_value": "translated string value"
    }

    for spec in ATTR_SPECS:
        attr = Attribute.objects.get(identifier=spec["identifier"])
        attr_data = {
            "numeric_value": None,
            "datetime_value": None,
            "untranslated_string_value": "",
            "attribute": attr.pk,
            # "product": product.pk
        }

        if attr.is_stringy:
            if attr.is_translated:
                attr_data["translations"] = {
                    "en": {
                        "translated_string_value": expected_values["translated_string_value"]
                    }
                }
            else:
                attr_data["untranslated_string_value"] = expected_values["untranslated_string_value"]
        elif attr.is_numeric:
            if attr.type == AttributeType.BOOLEAN:
                attr_data["numeric_value"] = int(expected_values["boolean_value"])
            elif attr.type == AttributeType.TIMEDELTA:
                attr_data["numeric_value"] = int(expected_values["timedelta_value"])
            else:
                attr_data["numeric_value"] = expected_values["numeric_value"]
        elif attr.is_temporal:
            attr_data["datetime_value"] = expected_values["datetime_value"]

        attributes_data.append(attr_data)

    data = _get_product_sample_data()
    data["shop_products"] = _get_sample_shop_product_data(shop, cat, supplier)
    data["attributes"] = attributes_data
    response = client.post("/api/shuup/product/", content_type="application/json", data=json.dumps(data))
    assert response.status_code == status.HTTP_201_CREATED

    # check all
    for lang in ("en", "pt-br"):
        activate(lang)
        product = Product.objects.first()
        _check_product_basic_data(product, data, lang)

    assert Product.objects.count() == 1
    assert ShopProduct.objects.count() == 1

    product = Product.objects.first()
    shop_product = ShopProduct.objects.first()

    assert product.get_shop_instance(shop) == shop_product
    assert supplier in shop_product.suppliers.all()
    assert cat in shop_product.categories.all()
    assert shop_product.primary_category == cat

    # validate attribute values
    for spec in ATTR_SPECS:
        attribute = Attribute.objects.get(identifier=spec["identifier"])
        attr = ProductAttribute.objects.get(product=product, attribute=attribute)
        if attribute.is_stringy:
            if attribute.is_translated:
                attr.set_current_language("en")
                assert attr.value == expected_values["translated_string_value"]
            else:
                assert attr.value == expected_values["untranslated_string_value"]
        elif attribute.is_numeric:
            if attribute.type == AttributeType.BOOLEAN:
                assert attr.value == expected_values["boolean_value"]
            elif attribute.type == AttributeType.TIMEDELTA:
                assert attr.value == datetime.timedelta(seconds=int(expected_values["timedelta_value"]))
            else:
                assert attr.value == expected_values["numeric_value"]
        elif attribute.is_temporal:
            dt_value = expected_values["datetime_value"]
            parsed_dt = dt.strptime(dt_value, "%Y-%m-%d %H:%M:%S")
            assert attr.value.year == parsed_dt.year
            assert attr.value.month == parsed_dt.month
            assert attr.value.day == parsed_dt.day


def test_update_product(admin_user):
    get_default_shop()
    product = create_product("test")
    client = _get_client(admin_user)
    data = _get_product_sample_data()
    response = client.put("/api/shuup/product/%d/" % product.pk, content_type="application/json", data=json.dumps(data))
    assert response.status_code == status.HTTP_200_OK

    # check whether the info was changed
    for lang in ("en", "pt-br"):
        activate(lang)
        product = Product.objects.first()
        _check_product_basic_data(product, data, lang)


def test_delete_product(admin_user):
    get_default_shop()
    client = _get_client(admin_user)

    assert Product.objects.count() == 0
    data = _get_product_sample_data()
    response = client.post("/api/shuup/product/", content_type="application/json", data=json.dumps(data))
    assert response.status_code == status.HTTP_201_CREATED
    assert Product.objects.count() == 1

    product = Product.objects.first()

    # actually, we do not remove it from db, just "soft delete"
    response = client.delete("/api/shuup/product/%d/" % product.pk, content_type="application/json")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    assert Product.objects.count() == 1

    # check whether the info was changed
    for lang in ("en", "pt-br"):
        activate(lang)
        product = Product.objects.first()
        _check_product_basic_data(product, data, lang)
        assert product.deleted is True


def test_create_shop_product(admin_user):
    shop = get_default_shop()
    client = _get_client(admin_user)

    assert Product.objects.count() == 0
    data = _get_product_sample_data()
    response = client.post("/api/shuup/product/", content_type="application/json", data=json.dumps(data))
    assert response.status_code == status.HTTP_201_CREATED
    product = Product.objects.first()
    assert ShopProduct.objects.count() == 0

    shop_data = _get_shop_product_sample_data()
    response = client.post("/api/shuup/product/%d/add_shop/" % product.id,
                           content_type="application/json",
                           data=json.dumps(shop_data))
    assert response.status_code == status.HTTP_201_CREATED
    assert ShopProduct.objects.count() == 1

    # verify shop product data
    for lang in ("en", "pt-br"):
        activate(lang)
        shop_product = ShopProduct.objects.first()
        _check_shop_product_basic_data(shop_product, shop_data, lang)


def test_product_add_attribute(admin_user):
    shop = get_default_shop()
    client = _get_client(admin_user)
    product = create_product("product1")

    attribute1 = Attribute.objects.create(identifier="attr1",
                                          type=AttributeType.BOOLEAN,
                                          visibility_mode=AttributeVisibility.SHOW_ON_PRODUCT_PAGE,
                                          name="Attribute 1")
    attribute2 = Attribute.objects.create(identifier="attr2",
                                          type=AttributeType.TRANSLATED_STRING,
                                          visibility_mode=AttributeVisibility.SHOW_ON_PRODUCT_PAGE,
                                          name="Attribute 2")
    attribute3 = Attribute.objects.create(identifier="attr3",
                                          type=AttributeType.UNTRANSLATED_STRING,
                                          visibility_mode=AttributeVisibility.SHOW_ON_PRODUCT_PAGE,
                                          name="Attribute 3")

    get_default_product_type().attributes.add(attribute1)
    get_default_product_type().attributes.add(attribute2)

    product_attr1_data = {
        "attribute": attribute1.pk,
        "numeric_value": 0,
    }
    response = client.post("/api/shuup/product/%d/add_attribute/" % product.pk,
                           content_type="application/json",
                           data=json.dumps(product_attr1_data))
    assert response.status_code == status.HTTP_201_CREATED
    assert ProductAttribute.objects.filter(product=product).count() == 1
    pa = ProductAttribute.objects.first()
    assert pa.attribute.pk == attribute1.pk
    assert pa.numeric_value == product_attr1_data["numeric_value"]

    product_attr2_data = {
        "attribute": attribute2.pk,
        "translations": {
            "en": {"translated_string_value": "come on"},
            "pt-br": {"translated_string_value": "vamos lá"}
        }
    }
    response = client.post("/api/shuup/product/%d/add_attribute/" % product.pk,
                           content_type="application/json",
                           data=json.dumps(product_attr2_data))
    assert response.status_code == status.HTTP_201_CREATED
    assert ProductAttribute.objects.filter(product=product).count() == 2
    pa = ProductAttribute.objects.last()
    assert pa.attribute.pk == attribute2.pk
    assert pa.translated_string_value == product_attr2_data["translations"]["en"]["translated_string_value"]

    # try to add an attribute which does not belong to the product type
    product_attr3_data = {
        "attribute": attribute3.pk,
        "untraslated_string": "lalala"
    }
    response = client.post("/api/shuup/product/%d/add_attribute/" % product.pk,
                           content_type="application/json",
                           data=json.dumps(product_attr3_data))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert ProductAttribute.objects.filter(product=product).count() == 2


def test_make_product_package(admin_user):
    shop = get_default_shop()
    client = _get_client(admin_user)
    product1 = create_product("product1")
    product2 = create_product("product2")
    product3 = create_product("product3")
    product4 = create_product("product4")
    assert product1.mode == product2.mode == product3.mode == product4.mode == ProductMode.NORMAL

    package_data = [
        {"product": product2.pk, "quantity":1},
        {"product": product3.pk, "quantity":2},
        {"product": product4.pk, "quantity":3.5}
    ]
    response = client.post("/api/shuup/product/%d/make_package/" % product1.pk,
                           content_type="application/json",
                           data=json.dumps(package_data))
    assert response.status_code == status.HTTP_201_CREATED
    product1.refresh_from_db()
    product2.refresh_from_db()
    product3.refresh_from_db()
    product4.refresh_from_db()
    assert product1.mode == ProductMode.PACKAGE_PARENT

    child1 = ProductPackageLink.objects.get(parent=product1, child=product2)
    assert child1.quantity == 1
    child2 = ProductPackageLink.objects.get(parent=product1, child=product3)
    assert child2.quantity == 2
    child3 = ProductPackageLink.objects.get(parent=product1, child=product4)
    assert child3.quantity == 3.5


def test_make_product_package_impossible(admin_user):
    shop = get_default_shop()
    client = _get_client(admin_user)
    product1 = create_product("product1")

    package_data = [
        {"product": product1.pk, "quantity":3.5}
    ]
    response = client.post("/api/shuup/product/%d/make_package/" % product1.pk,
                           content_type="application/json",
                           data=json.dumps(package_data))
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_product_package(admin_user):
    shop = get_default_shop()
    client = _get_client(admin_user)
    product1 = create_product("product1")
    product2 = create_product("product2")
    product3 = create_product("product3")
    product4 = create_product("product4")

    product1.make_package({product2: 1, product3: 2, product4: 3})
    product1.save()
    assert product1.mode == ProductMode.PACKAGE_PARENT

    package_child_links = ProductPackageLink.objects.filter(parent=product1)

    # get the first child
    response = client.get("/api/shuup/product_package/%d/" % package_child_links[0].id)
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert data["product"] == product2.id
    assert Decimal(data["quantity"]) == Decimal(1)
    assert data["id"] == package_child_links[0].id

    # get the 2nd child
    response = client.get("/api/shuup/product_package/%d/" % package_child_links[1].id)
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert data["product"] == product3.id
    assert Decimal(data["quantity"]) == Decimal(2)
    assert data["id"] == package_child_links[1].id

    # get the 3rd child
    response = client.get("/api/shuup/product_package/%d/" % package_child_links[2].id)
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert data["product"] == product4.id
    assert Decimal(data["quantity"]) == Decimal(3)
    assert data["id"] == package_child_links[2].id

    # update the first child - set quantity=10
    package_data = {"quantity": 10}
    response = client.put("/api/shuup/product_package/%d/" % package_child_links[0].id,
                          content_type="application/json",
                          data=json.dumps(package_data))
    assert response.status_code == status.HTTP_200_OK
    response = client.get("/api/shuup/product_package/%d/" % package_child_links[0].id)
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert data["product"] == product2.id
    assert Decimal(data["quantity"]) == Decimal(10)

    # deletes the last child
    response = client.delete("/api/shuup/product_package/%d/" % package_child_links[2].id)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert ProductPackageLink.objects.count() == 2


def test_product_attribute(admin_user):
    shop = get_default_shop()
    client = _get_client(admin_user)
    product1 = create_product("product1")

    attrib1 = create_random_product_attribute()
    attrib2 = create_random_product_attribute()
    product_type = get_default_product_type()
    product_type.attributes.add(attrib1)
    product_type.attributes.add(attrib2)

    product_attr1_data = {"attribute": attrib1.pk, "numeric_value": 0}
    product_attr2_data = {"attribute": attrib2.pk, "numeric_value": 1}
    response = client.post("/api/shuup/product/%d/add_attribute/" % product1.pk,
                           content_type="application/json",
                           data=json.dumps(product_attr1_data))
    assert response.status_code == status.HTTP_201_CREATED
    response = client.post("/api/shuup/product/%d/add_attribute/" % product1.pk,
                           content_type="application/json",
                           data=json.dumps(product_attr2_data))
    assert response.status_code == status.HTTP_201_CREATED

    attrs = ProductAttribute.objects.filter(product=product1)

    # get the first attr
    response = client.get("/api/shuup/product_attribute/%d/" % attrs[0].id)
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert data["product"] == product1.id
    assert data["attribute"] == attrib1.id
    assert Decimal(data["numeric_value"]) == Decimal(0)

    # get the 2nd attr
    response = client.get("/api/shuup/product_attribute/%d/" % attrs[1].id)
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert data["product"] == product1.id
    assert data["attribute"] == attrib2.id
    assert Decimal(data["numeric_value"]) == Decimal(1)

    # update the first attr - numeric_value=1, attr=2
    attr_data = {"numeric_value": 1, "attribute": attrib2.pk}
    response = client.put("/api/shuup/product_attribute/%d/" % attrs[0].id,
                          content_type="application/json",
                          data=json.dumps(attr_data))
    assert response.status_code == status.HTTP_200_OK
    response = client.get("/api/shuup/product_attribute/%d/" % attrs[0].id)
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content.decode("utf-8"))
    assert data["product"] == product1.id
    assert data["attribute"] == attrib2.id
    assert Decimal(data["numeric_value"]) == Decimal(1)

    # deletes the last attr
    response = client.delete("/api/shuup/product_attribute/%d/" % attrs[1].id)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert ProductAttribute.objects.count() == 1

def test_create_complete_product(admin_user):
    """
    Create category, product type, manufacturer, attributes, the product and after that,
    add cross sells, images, media and configure attributes
    EVERTYHING THROUGH REST API
    """
    get_default_shop()
    client = _get_client(admin_user)

    ###### 1) create attribute
    attribute_data = {
        "searchable": True,
        "type": AttributeType.INTEGER.value,
        "visibility_mode": AttributeVisibility.SHOW_ON_PRODUCT_PAGE.value,
        "translations": {
            "en": {"name": "Attribute Name"},
            "pt-br": {"name": "Nome do Atributo"},
        },
        "identifier": "attr1"
    }
    response = client.post("/api/shuup/attribute/", content_type="application/json", data=json.dumps(attribute_data))
    assert response.status_code == status.HTTP_201_CREATED
    attribute = Attribute.objects.first()

    ###### 2) crete product type
    product_type_data = {
        "translations": {
            "en": {"name": "Product type 1"},
            "pt-br": {"name": "Tipo do produto 1"},
        },
        "attributes": [attribute.pk]
    }
    response = client.post("/api/shuup/product_type/",
                           content_type="application/json",
                           data=json.dumps(product_type_data))
    assert response.status_code == status.HTTP_201_CREATED
    product_type = ProductType.objects.first()

    ###### 3) create manufacturer
    manufac_data = {
        "name": "manu 1",
        "url": "http://www.mamamia.com"
    }
    response = client.post("/api/shuup/manufacturer/", content_type="application/json", data=json.dumps(manufac_data))
    assert response.status_code == status.HTTP_201_CREATED
    manufacturer = Manufacturer.objects.first()

    ###### 4) create sales unit
    sales_unit_data = {
        "translations": {
            "en": {"name": "Kilo", "symbol": "KG"},
            "pt-br": {"name": "Quilo", "symbol": "KGz"},
        },
        "decimals": 2
    }
    response = client.post("/api/shuup/sales_unit/", content_type="application/json", data=json.dumps(sales_unit_data))
    assert response.status_code == status.HTTP_201_CREATED
    sales_unit = SalesUnit.objects.first()

    ###### 5) create tax class
    tax_class_data = {
        "translations": {
            "en": {"name": "Tax Class"},
            "pt-br": {"name": "Classe de Imposto"},
        },
        "enabled": True
    }
    response = client.post("/api/shuup/tax_class/", content_type="application/json", data=json.dumps(tax_class_data))
    assert response.status_code == status.HTTP_201_CREATED
    tax_class = TaxClass.objects.first()

    ###### 6) finally, create the product
    product_data = {
        "translations":{
            "en": {
                "name": "Product Name",
                "description": "Product Description",
                "slug": "product_sku",
                "keywords": "keyword1, k3yw0rd2",
                "status_text": "available soon",
                "variation_name": "Product RED"
            },
            "pt-br": {
                "name": "Nome do Produto",
                "description": "Descrição do Produto",
                "slug": "product_sku_em_portugues",
                "keywords": "chave1, chavez2",
                "status_text": "disponivel logo",
                "variation_name": "Produto Vermelho"
            }
        },
        "stock_behavior": StockBehavior.STOCKED.value,
        "shipping_mode": ShippingMode.SHIPPED.value,
        "sales_unit": sales_unit.pk,
        "tax_class": tax_class.pk,
        "type": product_type.pk,
        "sku": "sku12345",
        "gtin": "789456132",
        "barcode": "7896899123456",
        "accounting_identifier": "cbe6a7d67a8bdae",
        "profit_center": "prooofit!",
        "cost_center": "space ghost",
        "width": 150.0,
        "height": 230.0,
        "depth": 450.4,
        "net_weight": 13.2,
        "gross_weight": 20.3,
        "manufacturer": manufacturer.pk
    }
    response = client.post("/api/shuup/product/", content_type="application/json", data=json.dumps(product_data))
    product = Product.objects.first()
    assert product


def _get_shop_product_sample_data():
    return {
        "shop": get_default_shop().id,
        "suppliers": [
            get_default_supplier().id
        ],
        "visibility": ShopProductVisibility.ALWAYS_VISIBLE.value,
        "purchasable": False,
        "visibility_limit": ProductVisibility.VISIBLE_TO_ALL.value,
        "visibility_groups": [
            create_random_contact_group().id,
            create_random_contact_group().id,
        ],
        "backorder_maximum": 0,
        "purchase_multiple": 1,
        "minimum_purchase_quantity": 1,
        "limit_shipping_methods": False,
        "limit_payment_methods": False,
        "shipping_methods": [],
        "payment_methods": [],
        "primary_category": get_default_category().id,
        "categories": [
            get_default_category().id,
            CategoryFactory().id
        ],
        "default_price_value": 12.45,
        "minimum_price_value": 5.35,
        "translations": {
            "en": {
                "status_text": "available soon",
            },
            "pt-br": {
                "status_text": "disponivel logo",
            }
        },
    }


def _get_product_sample_data():
    return {
        # translations
        "translations":{
            "en": {
                "name": "Product Name",
                "description": "Product Description",
                "slug": "product_sku",
                "keywords": "keyword1, k3yw0rd2",
                "status_text": "available soon",
                "variation_name": "Product RED"
            },
            "pt-br": {
                "name": "Nome do Produto",
                "description": "Descrição do Produto",
                "slug": "product_sku_em_portugues",
                "keywords": "chave1, chavez2",
                "status_text": "disponivel logo",
                "variation_name": "Produto Vermelho"
            }
        },

        # others
        "stock_behavior": StockBehavior.STOCKED.value,
        "shipping_mode": ShippingMode.SHIPPED.value,
        "sales_unit": get_default_sales_unit().pk,
        "tax_class": get_default_tax_class().pk,
        "type": get_default_product_type().pk,
        "sku": "sku12345",
        "gtin": "789456132",
        "barcode": "7896899123456",
        "accounting_identifier": "cbe6a7d67a8bdae",
        "profit_center": "prooofit!",
        "cost_center": "space ghost",
        "width": 150.0,
        "height": 230.0,
        "depth": 450.4,
        "net_weight": 13.2,
        "gross_weight": 20.3
    }


def _get_sample_shop_product_data(shop, category, supplier):
    return [
        {
            "orderable": True,
            "visibility": 3,
            "visibility_limit": 1,
            "purchasable": True,
            "backorder_maximum": "0.000000000",
            "purchase_multiple": "0.000000000",
            "minimum_purchase_quantity": "1.000000000",
            "limit_shipping_methods": False,
            "limit_payment_methods": False,
            "default_price_value": "91.780000000",
            "shop": shop.pk,
            "primary_category": category.pk,
            "suppliers": [supplier.pk],
            "visibility_groups": [],
            "shipping_methods": [],
            "payment_methods": [],
            "categories": [category.pk]
        },
    ]


def _check_product_basic_data(product, data, lang="en"):
    precision = Decimal("0.01")

    assert product.name == data["translations"][lang]["name"]
    assert product.description == data["translations"][lang]["description"]
    assert product.slug == data["translations"][lang]["slug"]
    assert product.keywords == data["translations"][lang]["keywords"]
    assert product.variation_name == data["translations"][lang]["variation_name"]

    assert product.stock_behavior.value == data["stock_behavior"]
    assert product.shipping_mode.value == data["shipping_mode"]
    assert product.sales_unit.id == data["sales_unit"]
    assert product.tax_class.id == data["tax_class"]
    assert product.type.id == data["type"]
    assert product.sku == data["sku"]
    assert product.gtin == data["gtin"]
    assert product.barcode == data["barcode"]
    assert product.accounting_identifier == data["accounting_identifier"]
    assert product.profit_center == data["profit_center"]
    assert product.cost_center == data["cost_center"]
    assert product.width == Decimal(data["width"]).quantize(precision)
    assert product.height == Decimal(data["height"]).quantize(precision)
    assert product.depth == Decimal(data["depth"]).quantize(precision)
    assert product.net_weight == Decimal(data["net_weight"]).quantize(precision)
    assert product.gross_weight == Decimal(data["gross_weight"]).quantize(precision)


def _check_shop_product_basic_data(shop_product, data, lang="en"):
    precision = Decimal("0.01")

    assert shop_product.visibility.value == data["visibility"]
    assert shop_product.visibility_limit.value == data["visibility_limit"]
    assert shop_product.purchasable == data["purchasable"]

    assert shop_product.shop.id == data["shop"]
    assert shop_product.primary_category.id == data["primary_category"]
    assert shop_product.categories.first().pk == data["categories"][0]
    assert shop_product.suppliers.first().pk == data["suppliers"][0]
    assert shop_product.default_price_value == Decimal(data["default_price_value"]).quantize(precision)

    assert shop_product.status_text == data["translations"][lang]["status_text"]


def _get_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client
