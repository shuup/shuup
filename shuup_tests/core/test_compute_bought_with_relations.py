# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import pytest

from shuup.core.models import ProductCrossSell
from shuup.core.utils.product_bought_with_relations import (
    add_bought_with_relations_for_product
)
from shuup.testing.factories import (
    add_product_to_order, create_order_with_product, create_product,
    get_default_shop, get_default_supplier
)


@pytest.mark.django_db
def test_computing_simple_product_relations(rf):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product("simple-test-product", shop)
    related_product = create_product("simple-related-product", shop)
    quantities = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    for quantity in quantities:
        order = create_order_with_product(product, supplier, quantity=1, taxless_base_unit_price=6, shop=shop)
        add_product_to_order(order, supplier, related_product, quantity=quantity, taxless_base_unit_price=6)

    assert ProductCrossSell.objects.count() == 0
    add_bought_with_relations_for_product(product.pk)
    assert ProductCrossSell.objects.count() == 1
    cross_sell_product = ProductCrossSell.objects.filter(product1=product).first()
    assert cross_sell_product.product2 == related_product
    assert cross_sell_product.weight == sum(quantities)

    add_bought_with_relations_for_product(related_product.id)
    assert ProductCrossSell.objects.count() == 2
    cross_sell_product = ProductCrossSell.objects.filter(product1=related_product).first()
    assert cross_sell_product.product2 == product
    assert cross_sell_product.weight == len(quantities)


@pytest.mark.django_db
def test_product_relations_max_quantity(rf):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product("simple-test-product", shop)
    quantities = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    for i, quantity in enumerate(quantities):
        order = create_order_with_product(product, supplier, quantity=1, taxless_base_unit_price=6, shop=shop)
        add_product_to_order(
            order,
            supplier,
            create_product("product-%s" % i, shop),
            quantity=quantity,
            taxless_base_unit_price=6
        )

    assert ProductCrossSell.objects.count() == 0
    add_bought_with_relations_for_product(product.pk, max_quantity=5)
    assert ProductCrossSell.objects.count() == 5
    # Test that ordering is ok
    assert not ProductCrossSell.objects.filter(weight=1).exists()
    assert ProductCrossSell.objects.filter(weight=11).exists()
