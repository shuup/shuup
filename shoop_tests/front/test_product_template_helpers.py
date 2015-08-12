# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shoop.core import cache
from shoop.core.models.products import ProductCrossSell, ProductCrossSellType
from shoop.front.template_helpers.product import get_related_products
from shoop.testing.factories import create_product, get_default_shop
from shoop.testing.utils import apply_request_middleware
from shoop_tests.utils import printable_gibberish


@pytest.mark.django_db
def test_get_related_products(rf):
    cache.clear()  # Other tests may have put stuff in the cache. Let's not go there.
    shop = get_default_shop()
    source_product = create_product(printable_gibberish(), shop=shop)
    target_products = []
    for x in range(10):
        target_product = create_product(printable_gibberish(), shop=shop)
        target_products.append(target_product)
        ProductCrossSell.objects.create(
            product1=source_product, product2=target_product,
            type=ProductCrossSellType.RELATED, weight=x
        )

    context = {"request": apply_request_middleware(rf.get("/"))}

    count = 5
    result_products = get_related_products(context, source_product, "related", count)
    # Since weights are set by `x` in the above loop,
    # the `count` result products should be the `count` last products in the target product list:
    assert [p.pk for p in result_products] == [p.pk for p in target_products[:count]]
