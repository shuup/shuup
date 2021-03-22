# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import mock
import os
import pytest
from decimal import Decimal
from django.conf import settings
from django.utils.encoding import force_text
from django.utils.translation import activate
from six import BytesIO

from shuup.core.models import Category, Manufacturer, MediaFile, Product, ShopProduct
from shuup.default_importer.importers import ProductImporter
from shuup.importer.importing import DataImporter
from shuup.importer.transforms import transform_file
from shuup.importer.utils.importer import ImportMode
from shuup.simple_supplier.models import StockAdjustment
from shuup.testing.factories import (
    get_default_product_type,
    get_default_sales_unit,
    get_default_shop,
    get_default_supplier,
    get_default_tax_class,
    get_shop,
)
from shuup.testing.image_generator import generate_image
from shuup.utils.filer import filer_image_from_data

bom_file = "sample_import_bom.csv"
images_file = "sample_import_images.csv"


def _create_random_media_file(shop, file_path):
    path, name = os.path.split(file_path)
    pil_image = generate_image(2, 2)
    sio = BytesIO()
    pil_image.save(sio, "JPEG", quality=45)
    filer_file = filer_image_from_data(request=None, path=path, file_name=name, file_data=sio.getvalue())
    media_file = MediaFile.objects.create(file=filer_file)
    media_file.shops.add(shop)
    return media_file


@pytest.mark.parametrize(
    "filename",
    [
        "sample_import.xlsx",
        "sample_import.csv",
        "sample_import2.csv",
        "sample_import3.csv",
        "sample_import4.csv",
        "sample_import5.csv",
        "sample_import.xls",
        images_file,
        bom_file,
    ],
)
@pytest.mark.django_db
def test_sample_import_all_match(filename, rf):
    activate("en")
    shop = get_default_shop()
    tax_class = get_default_tax_class()
    product_type = get_default_product_type()
    sales_unit = get_default_sales_unit()

    path = os.path.join(os.path.dirname(__file__), "data", "product", filename)
    if filename == bom_file:
        import codecs

        bytes = min(32, os.path.getsize(path))
        raw = open(path, "rb").read(bytes)
        assert raw.startswith(codecs.BOM_UTF8)

    transformed_data = transform_file(filename.split(".")[1], path)
    importer = ProductImporter(
        transformed_data, ProductImporter.get_importer_context(rf.get("/"), shop=shop, language="en")
    )
    importer.process_data()

    if filename == images_file:
        _create_random_media_file(shop, "image1.jpeg")
        _create_random_media_file(shop, "products/images/image2.jpeg")
        _create_random_media_file(shop, "products/images/image3.jpeg")
        _create_random_media_file(shop, "image4.jpeg")
        _create_random_media_file(shop, "products2/images/image5.jpeg")
        _create_random_media_file(shop, "product1.jpeg")
        _create_random_media_file(shop, "products/images/product2.jpeg")
        _create_random_media_file(shop, "products/images2/product2.jpeg")

    importer.do_import(ImportMode.CREATE_UPDATE)
    products = importer.new_objects
    assert len(importer.log_messages) == 0

    if filename == images_file:
        assert len(products) == 3
    else:
        assert len(products) == 2

    for product in products:
        shop_product = product.get_shop_instance(shop)
        assert shop_product.pk
        assert shop_product.default_price_value == 150
        assert shop_product.default_price == shop.create_price(150)
        assert product.type == product_type  # product type comes from importer defaults
        assert product.sales_unit == sales_unit

        if product.pk == 1:
            assert product.tax_class.pk == 2  # new was created
            assert product.name == "Product English"
            assert product.description == "Description English"

            if filename == images_file:
                assert product.media.count() == 3
        elif product.pk == 2:
            assert product.tax_class.pk == tax_class.pk  # old was found as should
            assert product.name == "Product 2 English"
            assert product.description == "Description English 2"

            if filename == images_file:
                assert product.media.count() == 2
        elif product.pk == 3 and filename == images_file:
            assert product.media.count() == 3

        assert shop_product.primary_category.pk == 1
        assert [c.pk for c in shop_product.categories.all()] == [1, 2]


@pytest.mark.django_db
def test_sample_import_shop_relation(rf):
    activate("en")
    shop = get_default_shop()
    get_default_tax_class()
    get_default_product_type()
    get_default_sales_unit()

    path = os.path.join(os.path.dirname(__file__), "data", "product", "complex_import.xlsx")
    transformed_data = transform_file("xlsx", path)
    importer = ProductImporter(
        transformed_data, ProductImporter.get_importer_context(rf.get("/"), shop=shop, language="en")
    )
    importer.process_data()
    importer.do_import(ImportMode.CREATE_UPDATE)
    products = importer.new_objects

    for product in products:
        shop_product = product.get_shop_instance(shop)
        for category in shop_product.categories.all():
            assert shop in category.shops.all()

        if product.manufacturer:
            assert shop in product.manufacturer.shops.all()


@pytest.mark.parametrize(
    "filename",
    [
        "sample_import.xlsx",
        "sample_import.csv",
        "sample_import2.csv",
        "sample_import3.csv",
        "sample_import4.csv",
        "sample_import5.csv",
        "sample_import.xls",
    ],
)
@pytest.mark.django_db
def test_sample_import_all_match_all_shops(filename, rf):
    activate("en")
    shop1 = get_shop(identifier="shop1", domain="shop1", enabled=True)
    shop2 = get_shop(identifier="shop2", domain="shop2", enabled=True)
    Product.objects.all().delete()

    tax_class = get_default_tax_class()
    product_type = get_default_product_type()
    sales_unit = get_default_sales_unit()
    path = os.path.join(os.path.dirname(__file__), "data", "product", filename)
    transformed_data = transform_file(filename.split(".")[1], path)

    for shop in [shop1, shop2]:
        importer = ProductImporter(
            transformed_data, ProductImporter.get_importer_context(rf.get("/"), shop=shop, language="en")
        )
        importer.process_data()

        assert len(importer.unmatched_fields) == 0
        importer.do_import(ImportMode.CREATE_UPDATE)
        products = importer.new_objects

        if shop == shop1:
            # products created
            assert len(products) == 2
        else:
            # products already exist
            assert len(products) == 0

        assert Product.objects.count() == 2

        for product in Product.objects.all():
            shop_product = product.get_shop_instance(shop)
            assert shop_product.pk
            assert shop_product.default_price_value == 150
            assert shop_product.default_price == shop.create_price(150)
            assert product.type == product_type  # product type comes from importer defaults
            assert product.sales_unit == sales_unit

            assert shop_product.primary_category.pk == 1
            assert [c.pk for c in shop_product.categories.all()] == [1, 2]

    assert ShopProduct.objects.count() == 4


@pytest.mark.django_db
def test_sample_import_images_errors(rf):
    activate("en")
    shop = get_default_shop()
    get_default_tax_class()
    get_default_product_type()
    get_default_sales_unit()

    path = os.path.join(os.path.dirname(__file__), "data", "product", "sample_import_images_error.csv")
    transformed_data = transform_file("csv", path)
    importer = ProductImporter(
        transformed_data, ProductImporter.get_importer_context(rf.get("/"), shop=shop, language="en")
    )
    importer.process_data()

    importer.do_import(ImportMode.CREATE_UPDATE)
    assert len(importer.log_messages) == 2
    products = importer.new_objects
    assert len(products) == 2
    for product in products:
        assert not product.media.exists()


@pytest.mark.django_db
def test_sample_ignore_column(rf):
    activate("en")
    shop = get_default_shop()
    get_default_tax_class()
    get_default_product_type()
    get_default_sales_unit()

    path = os.path.join(os.path.dirname(__file__), "data", "product", "sample_import_ignore.csv")
    transformed_data = transform_file("csv", path)
    importer = ProductImporter(
        transformed_data, ProductImporter.get_importer_context(rf.get("/"), shop=shop, language="en")
    )
    importer.process_data()

    assert len(importer.unmatched_fields) == 0
    importer.do_import(ImportMode.CREATE_UPDATE)
    products = importer.new_objects
    assert len(products) == 2


@pytest.mark.parametrize("stock_managed", [True, False])
@pytest.mark.django_db
def test_sample_import_no_match(rf, stock_managed):
    filename = "sample_import_nomatch.xlsx"
    if "shuup.simple_supplier" not in settings.INSTALLED_APPS:
        pytest.skip("Need shuup.simple_supplier in INSTALLED_APPS")
    from shuup_tests.simple_supplier.utils import get_simple_supplier

    activate("en")
    shop = get_default_shop()
    tax_class = get_default_tax_class()
    product_type = get_default_product_type()
    supplier = get_simple_supplier(stock_managed)
    sales_unit = get_default_sales_unit()

    Manufacturer.objects.create(name="manufctr")
    path = os.path.join(os.path.dirname(__file__), "data", "product", filename)
    transformed_data = transform_file(filename.split(".")[1], path)

    importer = ProductImporter(
        transformed_data, ProductImporter.get_importer_context(rf.get("/"), shop=shop, language="en")
    )
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
        assert product.sales_unit == sales_unit
        if product.pk == 1:
            assert product.tax_class.pk == 2  # new was created
            assert product.name == "Product English"
            assert product.description == "Description English"
        else:
            assert product.tax_class.pk == tax_class.pk  # old was found as should
            assert product.name == "Product 2 English"
            assert product.description == "Description English 2"
        assert shop_product.primary_category.pk == 1
        assert [c.pk for c in shop_product.categories.all()] == [1, 2]

    # stock was not managed since supplier doesn't like that
    for msg in importer.other_log_messages:
        assert "please set `Stock Managed` on" in msg

    supplier.stock_managed = True
    supplier.save()
    importer.do_import("create,update")

    assert len(importer.other_log_messages) == 0
    for sa in StockAdjustment.objects.all():
        assert sa.product.pk
        assert sa.delta == 20


def import_categoryfile(rf, filename, expected_category_count, map_from=None, map_to=None):
    activate("en")
    shop = get_default_shop()
    get_default_tax_class()
    get_default_product_type()
    get_default_supplier()
    get_default_sales_unit()

    path = os.path.join(os.path.dirname(__file__), "data", "product", filename)
    transformed_data = transform_file(filename.split(".")[1], path)
    importer = ProductImporter(
        transformed_data, ProductImporter.get_importer_context(rf.get("/"), shop=shop, language="en")
    )
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
def test_proper_category_name(rf):
    import_categoryfile(rf, filename="proper_category_name.xlsx", expected_category_count=1)


@pytest.mark.django_db
def test_strange_category_name(rf):
    import_categoryfile(
        rf,
        filename="strange_category_name.xlsx",
        expected_category_count=1,
        map_from="mycat",
        map_to="shuup.core.models.ShopProduct:categories",
    )


@pytest.mark.django_db
def test_proper_category_names(rf):
    import_categoryfile(rf, filename="proper_categories.xlsx", expected_category_count=2)


@pytest.mark.django_db
def test_strange_category_names(rf):
    import_categoryfile(
        rf,
        filename="strange_categories.xlsx",
        expected_category_count=2,
        map_from="mycats",
        map_to="shuup.core.models.ShopProduct:categories",
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
        "manufacturer": "Shuup",
    },
    {
        "sku": "test-sku2",
        "name": '42" Plasma TV',
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
        "name": "VHS From 1980",
        "price": "115.65",
        "description": "This VHS comes with Robocop (uncut)",
        "categories": ["Televisions", "Perhipals"],
        "category": "Blu-ray Players",
        "product_type": "Perhipal",
        "visibility": "Always Visible",
        "tax_class": "Default Tax",
        "manufacturer": "RoboShuup",
    },
    {
        "sku": "test-sku4",
        "name": "Lamp",
        "price": "11500.555",
        "description": "Luxury lamp with pure gold",
        "categories": ["Perhipals", "Men"],
        "category": "Mancave",
        "product_type": "Mancave",
        "visibility": "Always Visible",
        "tax_class": "Cheap Tax",
        "manufacturer": "Golden Shuup",
    },
    {
        "sku": "test-sku5",
        "name": "Table",
        "price": "15500.552",
        "description": "Desk for the kings!",
        "categories": ["Men", "Space Age", "Expensive"],
        "category": "Mancave",
        "product_type": "Mancave",
        "visibility": "Searchable",
        "tax_class": "Cheap Tax",
        "manufacturer": "Shuup In Space",
    },
    {
        "sku": "test-sku6",
        "name": "Light Bulb",
        "price": "3",
        "description": "Light! Missing categories and manufacturer",
        "categories": None,
        "category": None,
        "product_type": "Mancave",
        "visibility": "Searchable",
        "tax_class": "Cheap Tax",
        "manufacturer": None,
    },
]


@pytest.mark.django_db
def test_complex_import(rf):
    filename = "complex_import.xlsx"
    activate("en")
    shop = get_default_shop()
    get_default_tax_class()
    get_default_product_type()
    get_default_supplier()
    get_default_sales_unit()

    path = os.path.join(os.path.dirname(__file__), "data", "product", filename)
    transformed_data = transform_file(filename.split(".")[1], path)
    importer = ProductImporter(
        transformed_data, ProductImporter.get_importer_context(rf.get("/"), shop=shop, language="en")
    )
    importer.process_data()

    assert len(importer.unmatched_fields) == 0
    importer.do_import(ImportMode.CREATE_UPDATE)
    products = importer.new_objects
    assert len(products) == 6
    assert ShopProduct.objects.count() == 6
    assert Category.objects.count() == 11
    assert Manufacturer.objects.count() == 4

    for idx, product in enumerate(Product.objects.all().order_by("sku")):
        shop_product = product.get_shop_instance(shop)

        data = PRODUCT_DATA[idx]
        assert product.sku == data["sku"]
        assert product.name == data["name"]

        assert shop_product.default_price_value == Decimal(data["price"])
        assert product.description == data["description"]

        if data.get("categories"):
            all_cats = set(data["categories"])
            all_cats.add(data["category"])

            for cat in shop_product.categories.all():
                assert cat.name in all_cats
            assert shop_product.categories.count() == len(all_cats)  # also add primary category

        if data.get("category"):
            assert shop_product.primary_category.name == data["category"]

        assert force_text(shop_product.visibility.label) == data["visibility"].lower()
        assert product.tax_class.name == data["tax_class"]

        if data.get("manufacturer"):
            assert product.manufacturer.name == data["manufacturer"]


def test_custom_transform_file():
    with mock.patch.object(DataImporter, "custom_file_transformer", True):
        with pytest.raises(NotImplementedError):
            DataImporter.transform_file("fake", "file name")
