# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.utils.encoding import force_text
from shoop.campaigns.models.catalog_filters import CategoryFilter, ProductFilter, ProductTypeFilter, CatalogFilter
from shoop.core.models import Category, ShopProduct
from shoop.testing.factories import get_default_category, create_product
from shoop_tests.campaigns import initialize_test


@pytest.mark.django_db
def test_category_filter(rf):
    request, shop, group = initialize_test(rf, False)

    cat = get_default_category()
    cat_filter = CategoryFilter.objects.create()
    cat_filter.categories.add(cat)
    cat_filter.save()

    assert cat_filter.values.first() == cat
    category = Category.objects.create(
        parent=None,
        identifier="testcat",
        name="catcat",
    )
    cat_filter.values = [cat, category]
    cat_filter.save()

    assert cat_filter.values.count() == 2

    product = create_product("Just-A-Product-Too", shop, default_price="200")
    shop_product = product.get_shop_instance(shop)
    shop_product.categories.add(cat)
    shop_product.save()

    assert cat_filter.filter_queryset(ShopProduct.objects.all()).exists()  # filter matches


@pytest.mark.django_db
def test_product_filter(rf):
    request, shop, group = initialize_test(rf, False)

    product = create_product("Just-A-Product-Too", shop, default_price="200")

    product_filter = ProductFilter.objects.create()
    product_filter.products.add(product)
    product_filter.save()

    assert product_filter.values.first() == product

    product2 = create_product("asdfasf", shop, default_price="20")
    product_filter.values = [product, product2]
    product_filter.save()

    assert product_filter.values.count() == 2

    assert product_filter.filter_queryset(ShopProduct.objects.all()).exists()  # filter matches


@pytest.mark.django_db
def test_product_type_filter(rf):
    request, shop, group = initialize_test(rf, False)

    product = create_product("Just-A-Product-Too", shop, default_price="200")

    product_type_filter = ProductTypeFilter.objects.create()
    product_type_filter.product_types.add(product.type)
    product_type_filter.save()

    assert product_type_filter.values.first() == product.type

    product2 = create_product("asdfasf", shop, default_price="20")
    product_type_filter.values = [product.type, product2.type]
    product_type_filter.save()

    assert product_type_filter.values.count() == 1  # both have same product type so only 1 value here

    assert product_type_filter.filter_queryset(ShopProduct.objects.all()).exists()  # filter matches

    assert product_type_filter.name.lower() in force_text(product_type_filter.description)
