# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shoop.core.models import PurchaseOrder
from shoop.simple_supplier.models import StockCount
from shoop.testing.factories import (
    create_order_with_product, create_product, get_default_product,
    get_default_shop, get_default_supplier
)
from shoop_tests.simple_supplier.utils import get_simple_supplier


@pytest.mark.django_db
def test_purchase_order_mark_as_arrived(rf, admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = get_default_product()
    order = create_order_with_product(product, supplier, 1, 200, shop=shop)
    purchase_order = PurchaseOrder(order_ptr_id=order.pk, manufacturer=product.manufacturer)
    purchase_order.__dict__.update(order.__dict__)
    purchase_order.save()

    with pytest.raises(NotImplementedError):
        purchase_order.mark_as_arrived(admin_user)  # base supplier module stock adjustment is not implemented

    supplier = get_simple_supplier()
    product = create_product("simple-test-product", shop, supplier)
    order = create_order_with_product(product, supplier, 1, 200, shop=shop)
    purchase_order = PurchaseOrder(order_ptr=order, manufacturer=product.manufacturer)
    purchase_order.__dict__.update(order.__dict__)
    purchase_order.save()
    stock = StockCount.objects.get(supplier=supplier, product=product)
    assert not purchase_order.is_complete()
    assert stock.logical_count == 1
    assert stock.physical_count == 0

    purchase_order.mark_as_arrived(admin_user)

    stock = StockCount.objects.get(supplier=supplier, product=product)
    assert purchase_order.is_complete()
    assert stock.logical_count == 1
    assert stock.physical_count == 1
