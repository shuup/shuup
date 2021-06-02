# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
import random

from shuup.core.models import AnonymousContact, Shipment, ShopProductVisibility
from shuup.core.signals import stocks_updated
from shuup.testing.factories import create_order_with_product, create_product, create_random_person, get_default_shop
from shuup.testing.receivers import shop_product_orderability_check
from shuup_tests.simple_supplier.utils import get_simple_supplier


@pytest.mark.parametrize("anonymous,hide_unorderable_product", [(True, True), (False, False)])
@pytest.mark.django_db
def test_simple_supplier_out_of_stock(rf, anonymous, hide_unorderable_product):
    if hide_unorderable_product:
        # Connect signal to hide products when they become unorderable
        stocks_updated.connect(receiver=shop_product_orderability_check, dispatch_uid="shop_product_orderability_check")

    supplier = get_simple_supplier()
    shop = get_default_shop()
    product = create_product("simple-test-product", shop, supplier)

    if anonymous:
        customer = AnonymousContact()
    else:
        customer = create_random_person()

    supplier.adjust_stock(product.pk, 0)
    ss = supplier.get_stock_status(product.pk)
    assert ss.product == product
    assert ss.logical_count == 0

    num = random.randint(100, 500)
    supplier.adjust_stock(product.pk, +num)
    assert supplier.get_stock_status(product.pk).logical_count == num

    shop_product = product.get_shop_instance(shop)

    if hide_unorderable_product:
        # Since the shop product save calls update stocks
        # and the fact that signal handler doesn't automatically
        # change visibility back means that the product is not
        # visible at this point.
        assert not shop_product.is_visible(customer)
        assert not shop_product.is_orderable(supplier, customer, 1, allow_cache=False)
        shop_product.visibility = ShopProductVisibility.ALWAYS_VISIBLE
        shop_product.save()

    assert shop_product.is_orderable(supplier, customer, 1, allow_cache=False)

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

    shop_product.refresh_from_db()
    if hide_unorderable_product:
        assert not shop_product.is_visible(customer)
        assert not shop_product.is_purchasable(supplier, customer, 1)
        assert not shop_product.is_orderable(supplier, customer, 1)
        # Disconnect signal just in case...
        stocks_updated.disconnect(
            receiver=shop_product_orderability_check, dispatch_uid="shop_product_orderability_check"
        )
    else:
        assert shop_product.is_visible(customer)
        assert not shop_product.is_purchasable(supplier, customer, 1)
        assert not shop_product.is_orderable(supplier, customer, 1)
