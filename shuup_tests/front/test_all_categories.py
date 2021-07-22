# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
import random
from bs4 import BeautifulSoup

from shuup.core.models import Category, CategoryStatus
from shuup.front.views.category import AllCategoriesView
from shuup.testing.factories import (
    create_product,
    get_default_category,
    get_default_product,
    get_default_shop,
    get_default_supplier,
)
from shuup.testing.utils import apply_request_middleware
from shuup_tests.utils import printable_gibberish


@pytest.mark.django_db
def test_all_categories_view(rf, reindex_catalog):
    shop = get_default_shop()
    supplier = get_default_supplier()
    category = get_default_category()
    product = get_default_product()
    request = apply_request_middleware(rf.get("/"))
    reindex_catalog()
    _check_product_count(request, 0)

    shop_product = product.get_shop_instance(shop)
    shop_product.categories.add(category)
    reindex_catalog()
    _check_product_count(request, 1)

    # Create few categories for better test results
    for i in range(10):
        cat = Category.objects.create(name=printable_gibberish())
        cat.shops.add(shop)

    new_product_count = random.randint(1, 3) + 1
    for i in range(1, new_product_count):
        product = create_product("sku-%s" % i, shop=shop, supplier=supplier, default_price=10)
        shop_product = product.get_shop_instance(shop)

        # Add random categories expect default category which we will make
        # hidden to make sure that products linked to hidden categories are
        # not listed
        shop_product.categories.set(Category.objects.exclude(id=category.pk).order_by("?")[:i])

    reindex_catalog()

    _check_product_count(request, new_product_count)

    category.status = CategoryStatus.INVISIBLE
    category.save()
    reindex_catalog()

    _check_product_count(request, new_product_count - 1)


def _check_product_count(request, expected_count):
    response = AllCategoriesView.as_view()(request)
    response.render()
    soup = BeautifulSoup(response.content, "lxml")
    assert len(soup.findAll("div", {"class": "single-product"})) == expected_count
