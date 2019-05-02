# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from collections import defaultdict
from decimal import Decimal

import pytest
import six

from shuup.core.excs import RefundExceedsAmountException
from shuup.core.models import OrderLine, OrderLineType, ShippingMode, Supplier
from shuup.testing.factories import (
    add_product_to_order, create_empty_order, create_product, get_default_shop
)


@pytest.mark.django_db
def test_order_refunds_with_multiple_suppliers():
    shop = get_default_shop()
    supplier1 = Supplier.objects.create(identifier="1", name="supplier1")
    supplier1.shops.add(shop)
    supplier2 = Supplier.objects.create(identifier="2")
    supplier2.shops.add(shop)
    supplier3 = Supplier.objects.create(identifier="3", name="s")
    supplier3.shops.add(shop)

    product1 = create_product("sku1", shop=shop, default_price=10)
    shop_product1 = product1.get_shop_instance(shop=shop)
    shop_product1.suppliers = [supplier1, supplier2, supplier3]

    product2 = create_product("sku2", shop=shop, default_price=10)
    shop_product2 = product1.get_shop_instance(shop=shop)
    shop_product2.suppliers = [supplier1, supplier2]

    product3 = create_product("sku3", shop=shop, default_price=10, shipping_mode=ShippingMode.NOT_SHIPPED)
    shop_product3 = product1.get_shop_instance(shop=shop)
    shop_product3.suppliers = [supplier3]

    product_quantities = {
        supplier1: {
            product1: 5,
            product2: 6
        },
        supplier2: {
            product1: 3,
            product2: 13
        },
        supplier3: {
            product1: 1,
            product3: 50
        }
    }

    def get_quantity(supplier, product):
        return product_quantities[supplier.pk][product.pk]

    order = create_empty_order(shop=shop)
    order.full_clean()
    order.save()

    for supplier, product_data in six.iteritems(product_quantities):
        for product, quantity in six.iteritems(product_data):
            add_product_to_order(order, supplier, product, quantity, 5)

    order.cache_prices()
    order.create_payment(order.taxful_total_price)
    assert order.is_paid()

    # All supplier should be able to refund the order
    assert order.can_create_refund()
    assert order.can_create_refund(supplier1)
    assert order.can_create_refund(supplier2)
    assert order.can_create_refund(supplier3)

    assert order.get_total_unrefunded_amount(supplier1).value == Decimal("55")  # 11 * 5
    assert order.get_total_unrefunded_quantity(supplier1) == Decimal("11")  # 5 x product1 and 6 x product2

    with pytest.raises(RefundExceedsAmountException):
        order.create_refund([{
            "line": "amount",
            "quantity": 1,
            "amount": order.shop.create_price(60)
        }], supplier=supplier1)

    # Supplier 1 refunds the order
    order.create_refund(_get_refund_data(order, supplier1))
    assert order.get_total_refunded_amount(supplier1).value  == Decimal("55")  # 11 * 5
    assert order.get_total_unrefunded_amount(supplier1).value == Decimal("0")

    assert not order.can_create_refund(supplier1)
    assert order.can_create_refund()
    assert order.can_create_refund(supplier2)
    assert order.can_create_refund(supplier3)

    assert order.get_total_unrefunded_amount(supplier2).value == Decimal("80")  # 16 * 5
    assert order.get_total_unrefunded_quantity(supplier2) == Decimal("16")  # 3 x product1 and 13 x product2

    with pytest.raises(RefundExceedsAmountException):
        order.create_refund([{
            "line": "amount",
            "quantity": 1,
            "amount": order.shop.create_price(81)
        }], supplier=supplier2)

    # Supplier 2 refunds the order
    order.create_refund(_get_refund_data(order, supplier2))
    assert order.get_total_refunded_amount(supplier2).value  == Decimal("80")  # 11 * 5
    assert order.get_total_unrefunded_amount(supplier2).value == Decimal("0")
    assert not order.can_create_refund(supplier1)
    assert not order.can_create_refund(supplier2)
    assert order.can_create_refund()
    assert order.can_create_refund(supplier3)

    assert order.get_total_unrefunded_amount(supplier3).value == Decimal("255")  # 51 * 5
    assert order.get_total_unrefunded_quantity(supplier3) == Decimal("51")  # 3 x product1 and 13 x product2

    order.create_refund([{
        "line": "amount",
        "quantity": 1,
        "amount": order.shop.create_price(200)
    }], supplier=supplier3)
    assert OrderLine.objects.filter(order=order, supplier=supplier3, type=OrderLineType.REFUND).exists()

    # Supplier 3 refunds the order
    order.create_refund(_get_refund_data(order, supplier3))
    assert order.get_total_refunded_amount(supplier3).value  == Decimal("255")  # 11 * 5
    assert order.get_total_unrefunded_amount(supplier3).value == Decimal("0")
    assert not order.can_create_refund(supplier1)
    assert not order.can_create_refund(supplier2)
    assert not order.can_create_refund(supplier3)
    assert not order.can_create_refund()


def _get_refund_data(order, supplier):
    return [
        {
            "line": line,
            "quantity": line.quantity,
            "amount": line.taxful_price.amount,
            "restock_products": True
        } for line in order.lines.filter(supplier=supplier)
    ]
