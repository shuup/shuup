# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os
from decimal import Decimal

import pytest
from django.utils.encoding import force_text
from django.utils.translation import activate

from shuup.core.models import Category, Manufacturer, Product, ShopProduct
from shuup.default_importer.importers import ProductImporter
from shuup.importer.transforms import transform_file
from shuup.importer.utils.importer import ImportMode
from shuup.simple_supplier.models import StockAdjustment
from shuup.testing.factories import (
    get_default_product_type, get_default_shop, get_default_supplier,
    get_default_tax_class
)

bom_file = "sample_import_bom.csv"

@pytest.mark.parametrize("filename", ["sample_import.xlsx", "sample_import.csv",
                                      "sample_import2.csv", "sample_import3.csv",
                                      "sample_import4.csv", "sample_import5.csv",
                                      "sample_import.xls", bom_file])
@pytest.mark.django_db
def test_sample_import_all_match(filename):
    activate("en")
    shop = get_default_shop()
    tax_class = get_default_tax_class()
    product_type = get_default_product_type()

    path = os.path.join(os.path.dirname(__file__), "data", "product", filename)
    if filename == bom_file:
        import codecs
        bytes = min(32, os.path.getsize(path))
        raw = open(path, 'rb').read(bytes)
        assert raw.startswith(codecs.BOM_UTF8)

    transformed_data = transform_file(filename.split(".")[1], path)
    importer = ProductImporter(transformed_data, shop, "en")
    importer.process_data()
    assert len(importer.unmatched_fields) == 0
    importer.do_import(ImportMode.CREATE_UPDATE)
    products = importer.new_objects
    assert len(products) == 2
    for product in products:
        shop_product = product.get_shop_instance(shop)
        assert shop_product.pk
        assert shop_product.default_price_value == 150
        assert shop_product.default_price == shop.create_price(150)
        assert product.type == product_type  # product type comes from importer defaults
        if product.pk == 1:
            assert product.tax_class.pk == 2  # new was created
            assert product.name == "Product English"
            assert product.description == "Description English"
        else:
            assert product.tax_class.pk == tax_class.pk  # old was found as should
            assert product.name == "Product 2 English"
            assert product.description == "Description English 2"
        assert shop_product.primary_category.pk == 1
        assert [c.pk for c in shop_product.categories.all()] == [1,2]

@pytest.mark.parametrize("stock_managed", [True, False])
@pytest.mark.django_db
def test_sample_import_no_match(stock_managed):
    filename = "sample_import_nomatch.xlsx"
    activate("en")
    shop = get_default_shop()
    tax_class = get_default_tax_class()
    product_type = get_default_product_type()
    supplier = get_default_supplier()
    supplier.stock_managed = stock_managed
    supplier.save()

    manufacturer = Manufacturer.objects.create(name="manufctr")
    path = os.path.join(os.path.dirname(__file__), "data", "product", filename)
    transformed_data = transform_file(filename.split(".")[1], path)

    importer = ProductImporter(transformed_data, shop, "en")
    importer.process_data()
    assert len(importer.unmatched_fields) == 1
    assert "gtiin" in importer.unmatched_fields
    importer.manually_match("gtiin", "shuup.core.models.Product:gtin")
    importer.do_remap()
    assert len(importer.unmatched_fields) == 0
    importer.do_import(ImportMode.CREATE_UPDATE)
    products = importer.new_objects
    assert len(products) == 2

    for product in products:
        assert product.gtin == "1280x720"
        shop_product = product.get_shop_instance(shop)
        assert shop_product.pk
        assert shop_product.default_price_value == 150
        assert shop_product.default_price == shop.create_price(150)
        assert product.type == product_type  # product type comes from importer defaults
        if product.pk == 1:
            assert product.tax_class.pk == 2  # new was created
            assert product.name == "Product English"
            assert product.description == "Description English"
        else:
            assert product.tax_class.pk == tax_class.pk  # old was found as should
            assert product.name == "Product 2 English"
            assert product.description == "Description English 2"
        assert shop_product.primary_category.pk == 1
        assert [c.pk for c in shop_product.categories.all()] == [1,2]

    # stock was not managed since supplier doesn't like that
    for msg in importer.other_log_messages:
        assert "please set Stock Managed on" in msg

    supplier.stock_managed = True
    supplier.save()
    importer.do_import("create,update")

    assert len(importer.other_log_messages) == 0
    for sa in StockAdjustment.objects.all():
        assert sa.product.pk
        assert sa.delta == 20


def import_categoryfile(filename, expected_category_count, map_from=None, map_to=None):
    activate("en")
    shop = get_default_shop()
    get_default_tax_class()
    get_default_product_type()
    get_default_supplier()

    path = os.path.join(os.path.dirname(__file__), "data", "product", filename)
    transformed_data = transform_file(filename.split(".")[1], path)
    importer = ProductImporter(transformed_data, shop, "en")
    importer.process_data()
    if map_from:
        assert len(importer.unmatched_fields) == 1
        assert map_from in importer.unmatched_fields
        importer.manually_match(map_from, map_to)
        importer.do_remap()
    else:
        assert len(importer.unmatched_fields) == 0
    importer.do_import(ImportMode.CREATE_UPDATE)
    products = importer.new_objects
    assert Category.objects.count() == expected_category_count


@pytest.mark.django_db
def test_proper_category_name():
    import_categoryfile(filename="proper_category_name.xlsx", expected_category_count=1)


@pytest.mark.django_db
def test_strange_category_name():
    import_categoryfile(
        filename="strange_category_name.xlsx",
        expected_category_count=1,
        map_from="mycat",
        map_to="shuup.core.models.ShopProduct:categories"
    )


@pytest.mark.django_db
def test_proper_category_names():
    import_categoryfile(filename="proper_categories.xlsx", expected_category_count=2)


@pytest.mark.django_db
def test_strange_category_names():
    import_categoryfile(
        filename="strange_categories.xlsx",
        expected_category_count=2,
        map_from="mycats",
        map_to="shuup.core.models.ShopProduct:categories"
    )

PRODUCT_DATA = [
    {
        "sku": "test-sku1",
        "name": "Camcorder Battery",
        "price": "252",
        "description": "Best Camcorder in the market",
        "categories": ["Batteries", "Cam Corders", "Perhipals"],
        "category": "Electronics",
        "product_type": "Perhipal",
        "visibility": "Always Visible",
        "tax_class": "Default Tax",
        "manufacturer": "Shuup"
    },
    {
        "sku": "test-sku2",
        "name": "42\" Plasma TV",
        "price": "120.22",
        "description": "This huge <b>TV</b> Has plasma in it",
        "categories": ["Televisions", "Plasma TV's"],
        "category": "Televisions",
        "product_type": "Television",
        "visibility": "Always Visible",
        "tax_class": "Default Tax",
        "manufacturer": "Shuup",
    },
    {
        "sku": "test-sku3",
        "name":"VHS From 1980",
        "price":"115.65",
        "description":"This VHS comes with Robocop (uncut)",
        "categories": ["Televisions", "Perhipals"],
        "category":"Blu-ray Players",
        "product_type":"Perhipal",
        "visibility":"Always Visible",
        "tax_class":"Default Tax",
        "manufacturer":"RoboShuup"
    },
    {
        "sku": "test-sku4",
        "name":"Lamp",
        "price":"11500.555",
        "description":"Luxury lamp with pure gold",
        "categories": ["Perhipals", "Men"],
        "category":"Mancave",
        "product_type":"Mancave",
        "visibility":"Always Visible",
        "tax_class":"Cheap Tax",
        "manufacturer":"Golden Shuup"
    },
    {
        "sku": "test-sku5",
        "name":"Table",
        "price":"15500.552",
        "description":"Desk for the kings!",
        "categories": ["Men", "Space Age", "Expensive"],
        "category":"Mancave",
        "product_type":"Mancave",
        "visibility":"Searchable",
        "tax_class":"Cheap Tax",
        "manufacturer":"Shuup In Space"
    }
]
@pytest.mark.django_db
def test_complex_import():
    filename = "complex_import.xlsx"
    activate("en")
    shop = get_default_shop()
    get_default_tax_class()
    get_default_product_type()
    get_default_supplier()

    path = os.path.join(os.path.dirname(__file__), "data", "product", filename)
    transformed_data = transform_file(filename.split(".")[1], path)
    importer = ProductImporter(transformed_data, shop, "en")
    importer.process_data()

    assert len(importer.unmatched_fields) == 0
    importer.do_import(ImportMode.CREATE_UPDATE)
    products = importer.new_objects
    assert len(products) == 5
    assert ShopProduct.objects.count() == 5
    assert Category.objects.count() == 11
    assert Manufacturer.objects.count() == 4

    for idx, product in enumerate(Product.objects.all().order_by("sku")):
        shop_product = product.get_shop_instance(shop)

        data = PRODUCT_DATA[idx]
        assert product.sku == data["sku"]
        assert product.name == data["name"]

        assert shop_product.default_price_value == Decimal(data["price"])
        assert product.description == data["description"]
        all_cats = set(data["categories"])
        all_cats.add(data["category"])

        for cat in shop_product.categories.all():
            assert cat.name in all_cats
        assert shop_product.categories.count() == len(all_cats)  # also add primary category
        assert shop_product.primary_category.name == data["category"]
        assert force_text(shop_product.visibility.label) == data["visibility"].lower()
        assert product.tax_class.name == data["tax_class"]
        assert product.manufacturer.name == data["manufacturer"]
