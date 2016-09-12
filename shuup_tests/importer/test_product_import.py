# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import os

import pytest
from django.utils.translation import activate

from shuup.core.models import Manufacturer
from shuup.default_importer.importers import ProductImporter
from shuup.importer.transforms import transform_file
from shuup.importer.utils.importer import ImportMode
from shuup.simple_supplier.models import StockAdjustment
from shuup.testing.factories import (
    get_default_product_type, get_default_shop, get_default_supplier,
    get_default_tax_class
)


@pytest.mark.parametrize("filename", ["sample_import.xlsx", "sample_import.csv",
                                      "sample_import2.csv", "sample_import3.csv",
                                      "sample_import4.csv", "sample_import5.csv",
                                      "sample_import.xls"])
@pytest.mark.django_db
def test_sample_import_all_match(filename):
    activate("en")
    shop = get_default_shop()
    tax_class = get_default_tax_class()
    product_type = get_default_product_type()

    path = os.path.join(os.path.dirname(__file__), "data", "product", filename)
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
        assert shop_product.pk == product.pk
        assert shop_product.default_price_value == 150
        assert shop_product.default_price == shop.create_price(150)
        assert shop_product.primary_image.pk
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


@pytest.mark.django_db
def test_sample_import_no_match():
    filename = "sample_import_nomatch.xlsx"
    activate("en")
    shop = get_default_shop()
    tax_class = get_default_tax_class()
    product_type = get_default_product_type()
    supplier = get_default_supplier()
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
        assert shop_product.pk == product.pk  # new shop product created for all products
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
