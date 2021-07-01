# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from decimal import Decimal

from shuup.core.catalog import ProductCatalog, ProductCatalogContext
from shuup.testing import factories


def test_product_catalog_simple_list():
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()
    product1 = factories.create_product("p1", shop=shop, supplier=supplier, default_price=Decimal("30"))
    product2 = factories.create_product("p2", shop=shop, supplier=supplier, default_price=Decimal("10"))
    product3 = factories.create_product("p3", shop=shop, supplier=supplier, default_price=Decimal("20"))

    context = ProductCatalogContext()
    catalog = ProductCatalog(context)

    # return a Product queryset annotated with price and discounted price
    products_qs = catalog.get_products_queryset().order_by("catalog_price")
    expected_prices = [
        (product2.pk, Decimal("10"), Decimal("10")),
        (product3.pk, Decimal("20"), Decimal("20")),
        (product1.pk, Decimal("30"), Decimal("30")),
    ]
    values = products_qs.values_list("pk", "catalog_price", "catalog_discounted_price")
    for index, value in enumerate(values):
        assert value == expected_prices[index]

    # return a ShopProduct queryset, annotated with price and discounted price
    expected_prices = [
        (product2.get_shop_product(shop).pk, Decimal("10"), Decimal("10")),
        (product3.get_shop_product(shop).pk, Decimal("20"), Decimal("20")),
        (product1.get_shop_product(shop).pk, Decimal("30"), Decimal("30")),
    ]
    shop_products_qs = catalog.get_shop_products_queryset()
    values = shop_products_qs.values_list("pk", "catalog_price", "catalog_discounted_price")
    for index, value in enumerate(values):
        assert value == expected_prices[index]
