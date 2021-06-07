# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.core.models import Shipment, ShipmentProduct, ShipmentStatus, ShipmentType
from shuup.testing.factories import create_product, get_default_shop
from shuup_tests.simple_supplier.utils import get_simple_supplier


@pytest.mark.django_db
def test_simple_supplier(rf):
    supplier = get_simple_supplier()
    shop = get_default_shop()
    product = create_product("simple-test-product", shop)
    ss = supplier.get_stock_status(product.pk)
    assert ss.logical_count == 0
    supplier.adjust_stock(product.pk, 0)
    ss = supplier.get_stock_status(product.pk)
    assert ss.product == product
    assert ss.logical_count == 0

    product_qty = 5
    shipment = Shipment.objects.create(supplier=supplier, type=ShipmentType.IN)
    ShipmentProduct.objects.create(shipment=shipment, product=product, quantity=product_qty)

    assert shipment.status == ShipmentStatus.NOT_SENT

    shipment.set_received()
    assert shipment.status == ShipmentStatus.RECEIVED

    ss = supplier.get_stock_status(product.pk)
    assert ss.product == product
    assert ss.logical_count == 5
