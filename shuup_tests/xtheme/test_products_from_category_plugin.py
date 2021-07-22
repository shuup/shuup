# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from bs4 import BeautifulSoup

from shuup.core.models import Category
from shuup.testing.factories import create_product, get_default_shop, get_default_supplier
from shuup.xtheme.plugins.products import ProductsFromCategoryPlugin
from shuup_tests.front.fixtures import get_jinja_context

CATEGORY_PRODUCT_DATA = [
    ("Test Product", "test-sku-1", 123),
    ("A Test Product", "test-sku-2", 720),
    ("XTest Product", "test-sku-3", 1),
    ("Fourth Test Product", "test-sku-4", 1),
    ("Last Test Product", "test-sku-5", 1),
]


@pytest.mark.django_db
def test_products_from_category_plugin(reindex_catalog):
    shop = get_default_shop()
    cat = Category.objects.create(identifier="cat-1")
    for name, sku, price in CATEGORY_PRODUCT_DATA:
        product = _create_orderable_product(name, sku, price=price)
        shop_product = product.get_shop_instance(shop)
        cat = Category.objects.first()
        shop_product.primary_category = cat
        shop_product.save()
        shop_product.categories.add(cat)

    reindex_catalog()
    context = get_jinja_context()
    rendered = ProductsFromCategoryPlugin({"title": "Products", "count": 4, "category": cat.id}).render(context)
    soup = BeautifulSoup(rendered, "lxml")
    assert "Products" in soup.find("h2").contents[0]
    assert len(soup.findAll("div", {"class": "product-card"})) == 4


def _create_orderable_product(name, sku, price):
    supplier = get_default_supplier()
    shop = get_default_shop()
    product = create_product(sku=sku, shop=shop, supplier=supplier, default_price=price, name=name)
    return product
