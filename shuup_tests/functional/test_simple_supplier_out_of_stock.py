# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import random

import pytest

from shuup.core.models import AnonymousContact, Shipment, StockBehavior
from shuup.testing.factories import (
    create_order_with_product, create_product, create_random_person,
    get_default_shop
)
from shuup_tests.simple_supplier.utils import get_simple_supplier


@pytest.mark.parametrize("anonymous", [True, False])
@pytest.mark.django_db
def test_simple_supplier_out_of_stock(rf, anonymous):
    supplier = get_simple_supplier()
    shop = get_default_shop()
    product = create_product("simple-test-product", shop, supplier, stock_behavior=StockBehavior.STOCKED)

    if anonymous:
        customer = AnonymousContact()
    else:
        customer = create_random_person()

    ss = supplier.get_stock_status(product.pk)
    assert ss.product == product
    assert ss.logical_count == 0
    num = random.randint(100, 500)
    supplier.adjust_stock(product.pk, +num)
    assert supplier.get_stock_status(product.pk).logical_count == num

    shop_product = product.get_shop_instance(shop)
    assert shop_product.is_orderable(supplier, customer, 1)

    # Create order
    order = create_order_with_product(product, supplier, num, 3, shop=shop)
    order.get_product_ids_and_quantities()
    pss = supplier.get_stock_status(product.pk)
    assert pss.logical_count == 0
    assert pss.physical_count == num

    assert not shop_product.is_orderable(supplier, customer, 1)

    # Create shipment
    shipment = order.create_shipment_of_all_products(supplier)
    assert isinstance(shipment, Shipment)
    pss = supplier.get_stock_status(product.pk)
    assert pss.logical_count == 0
    assert pss.physical_count == 0

    assert not shop_product.is_orderable(supplier, customer, 1)
