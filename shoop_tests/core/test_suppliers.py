# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shoop.core.models import StockBehavior
from shoop.testing.factories import (
    create_random_person, get_default_shop, get_default_shop_product, get_default_supplier
)


@pytest.mark.django_db
def test_default_supplier():
    supplier = get_default_supplier()
    shop_product = get_default_shop_product()
    product = shop_product.product
    assert supplier.get_stock_statuses([product.id])[product.id].logical_count == 0
    assert not list(supplier.get_orderability_errors(shop_product, 1, customer=None))


@pytest.mark.django_db
def test_get_suppliable_products():
    customer = create_random_person()
    shop_product = get_default_shop_product()
    shop = get_default_shop()
    supplier = get_default_supplier()
    # Check for default orderable shop product with unstocked behavior
    assert len(list(supplier.get_suppliable_products(shop, customer=customer))) == 1

    product = shop_product.product
    product.stock_behavior = StockBehavior.STOCKED
    product.save()
    # Make sure supplier now omits unorderable product
    assert not list(supplier.get_suppliable_products(shop, customer=customer))
