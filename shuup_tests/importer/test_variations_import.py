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
from django.utils.translation import activate
from six import BytesIO

from shuup.core.models import MediaFile, Product, ProductMode, ShopProduct, Supplier
from shuup.default_importer.importers import ProductImporter
from shuup.importer.transforms import transform_file
from shuup.importer.utils.importer import ImportMode
from shuup.testing.factories import (
    get_default_product_type,
    get_default_sales_unit,
    get_default_shop,
    get_default_tax_class,
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


@pytest.mark.django_db
def test_variatins_import(rf):
    filename = "product_sample_import_with_variations.xlsx"
    if "shuup.simple_supplier" not in settings.INSTALLED_APPS:
        pytest.skip("Need shuup.simple_supplier in INSTALLED_APPS")

    from shuup_tests.simple_supplier.utils import get_simple_supplier

    activate("en")
    shop = get_default_shop()
    product_type = get_default_product_type()
    sales_unit = get_default_sales_unit()
    tax_class = get_default_tax_class()

    # Create media
    _create_random_media_file(shop, "shirt1.jpeg")
    _create_random_media_file(shop, "shirt2.jpeg")
    _create_random_media_file(shop, "shirt3.jpeg")

    path = os.path.join(os.path.dirname(__file__), "data", "product", filename)
    transformed_data = transform_file(filename.split(".")[1], path)

    importer = ProductImporter(
        transformed_data, ProductImporter.get_importer_context(rf.get("/"), shop=shop, language="en")
    )
    importer.process_data()

    assert len(importer.unmatched_fields) == 0

    importer.do_import(ImportMode.CREATE_UPDATE)
    products = importer.new_objects

    assert len(products) == 42  # 2 parents 20 variations each

    supplier = Supplier.objects.first()
    assert supplier and supplier.stock_managed
    assert supplier.supplier_modules.filter(module_identifier="simple_supplier").exists()
    assert ShopProduct.objects.filter(suppliers=supplier).count() == 42

    parent1 = Product.objects.filter(sku=1).first()
    assert parent1.mode == ProductMode.VARIABLE_VARIATION_PARENT
    assert parent1.variation_children.all().count() == 20

    # Check product names
    child1 = Product.objects.filter(sku=10).first()
    assert child1.name == "T-Shirt - Pink - S"

    child2 = Product.objects.filter(sku=11).first()
    assert child2.name == "T-Shirt - Pink - XS"

    # Check stock counts
    assert supplier.get_stock_status(child1.pk).logical_count == Decimal(5)
    assert supplier.get_stock_status(child2.pk).logical_count == Decimal(10)

    parent2 = Product.objects.filter(sku=22).first()
    assert parent1.mode == ProductMode.VARIABLE_VARIATION_PARENT
    assert parent1.variation_children.all().count() == 20

    # Check product names
    child1 = Product.objects.filter(sku=38).first()
    assert child1.name == "Custom T-Shirt - Black - XL"

    child2 = Product.objects.filter(sku=39).first()
    assert child2.name == "Custom T-Shirt - Black - L"

    # Check stock counts
    assert supplier.get_stock_status(child1.pk).logical_count == Decimal(5)
    assert supplier.get_stock_status(child2.pk).logical_count == Decimal(10)

    path = os.path.join(
        os.path.dirname(__file__), "data", "product", "product_sample_import_with_variations_update.xlsx"
    )
    transformed_data = transform_file(filename.split(".")[1], path)

    importer = ProductImporter(
        transformed_data, ProductImporter.get_importer_context(rf.get("/"), shop=shop, language="en")
    )
    importer.process_data()

    assert len(importer.unmatched_fields) == 0

    importer.do_import(ImportMode.CREATE_UPDATE)
    products = importer.new_objects

    assert len(products) == 0

    updated_products = importer.updated_objects

    assert len(updated_products) == 4

    # Check product names
    child1 = Product.objects.filter(sku=10).first()
    assert child1.name == "T-Shirt - Pink - S"

    child2 = Product.objects.filter(sku=11).first()
    assert child2.name == "Test"

    # Check stock counts
    assert supplier.get_stock_status(child1.pk).logical_count == Decimal(5)
    assert supplier.get_stock_status(child2.pk).logical_count == Decimal(
        20
    )  # Did not add 20 but made the logical to 20

    parent2 = Product.objects.filter(sku=22).first()
    assert parent1.mode == ProductMode.VARIABLE_VARIATION_PARENT
    assert parent1.variation_children.all().count() == 20

    # Check product names
    child1 = Product.objects.filter(sku=38).first()
    assert child1.name == "Custom T-Shirt - Black - XL"

    child2 = Product.objects.filter(sku=39).first()
    assert child2.name == "Custom T-Shirt - Black - L"

    # Check stock counts
    assert supplier.get_stock_status(child1.pk).logical_count == Decimal(15)
    assert supplier.get_stock_status(child2.pk).logical_count == Decimal(10)

    # Test file with missing variations
    path = os.path.join(
        os.path.dirname(__file__), "data", "product", "product_sample_import_with_variations_missing_variables.xlsx"
    )
    transformed_data = transform_file(filename.split(".")[1], path)

    importer = ProductImporter(
        transformed_data, ProductImporter.get_importer_context(rf.get("/"), shop=shop, language="en")
    )
    importer.process_data()

    assert len(importer.unmatched_fields) == 0

    importer.do_import(ImportMode.CREATE_UPDATE)
    products = importer.new_objects

    assert len(products) == 0

    updated_products = importer.updated_objects

    assert len(updated_products) == 4

    for log_message in importer.log_messages:
        assert "Parent SKU set for the row, but no variation" in log_message["messages"][0]

    # check that both variation products still looks correct
    parent1 = Product.objects.filter(sku=1).first()
    assert parent1.mode == ProductMode.VARIABLE_VARIATION_PARENT
    assert parent1.variation_children.all().count() == 20

    parent2 = Product.objects.filter(sku=22).first()
    assert parent1.mode == ProductMode.VARIABLE_VARIATION_PARENT
    assert parent1.variation_children.all().count() == 20
