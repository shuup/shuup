# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from decimal import Decimal
from django.utils.encoding import force_text

from shuup.campaigns.models import CatalogCampaign
from shuup.campaigns.models.catalog_filters import (
    CatalogFilter, CategoryFilter, ProductFilter, ProductTypeFilter
)
from shuup.campaigns.models.product_effects import ProductDiscountPercentage
from shuup.core.models import Category, ShopProduct
from shuup.front.basket import get_basket
from shuup.testing.factories import create_product, get_default_category, get_default_supplier
from shuup_tests.campaigns import initialize_test
from shuup_tests.utils import printable_gibberish


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


@pytest.mark.django_db
def test_productfilter_works(rf):
    request, shop, group = initialize_test(rf, False)
    price = shop.create_price
    product_price = "100"
    discount_percentage = "0.30"

    supplier = get_default_supplier()
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=product_price)
    shop_product = product.get_shop_instance(shop)

    # create catalog campaign
    catalog_filter = ProductFilter.objects.create()
    catalog_filter.products.add(product)

    assert catalog_filter.matches(shop_product)

    catalog_campaign = CatalogCampaign.objects.create(shop=shop, active=True, name="test")
    catalog_campaign.filters.add(catalog_filter)
    cdp = ProductDiscountPercentage.objects.create(campaign=catalog_campaign, discount_percentage=discount_percentage)

    # add product to basket
    basket = get_basket(request)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)
    basket.save()

    expected_total = price(product_price) - (Decimal(discount_percentage) * price(product_price))
    assert basket.total_price == expected_total
