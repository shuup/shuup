# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
import six
from collections import defaultdict
from decimal import Decimal
from django.test import override_settings

from shuup.core.excs import RefundArbitraryRefundsNotAllowedException, RefundExceedsAmountException
from shuup.core.models import OrderLine, OrderLineType, ShippingMode, Supplier
from shuup.testing.factories import (
    add_product_to_order,
    create_empty_order,
    create_product,
    get_default_shop,
    get_supplier,
)


@pytest.mark.django_db
def test_order_refunds_with_multiple_suppliers():
    shop = get_default_shop()
    supplier1 = get_supplier("simple_supplier", shop=shop, identifier="1", name="supplier1")
    supplier2 = get_supplier("simple_supplier", shop=shop, identifier="2", name="supplier2")
    supplier3 = get_supplier("simple_supplier", shop=shop, identifier="3", name="s")

    product1 = create_product("sku1", shop=shop, default_price=10)
    shop_product1 = product1.get_shop_instance(shop=shop)
    shop_product1.suppliers.set([supplier1, supplier2, supplier3])

    product2 = create_product("sku2", shop=shop, default_price=10)
    shop_product2 = product1.get_shop_instance(shop=shop)
    shop_product2.suppliers.set([supplier1, supplier2])

    product3 = create_product("sku3", shop=shop, default_price=10, shipping_mode=ShippingMode.NOT_SHIPPED)
    shop_product3 = product1.get_shop_instance(shop=shop)
    shop_product3.suppliers.set([supplier3])

    product_quantities = {
        supplier1: {product1: 5, product2: 6},
        supplier2: {product1: 3, product2: 13},
        supplier3: {product1: 1, product3: 50},
    }

    def get_quantity(supplier, product):
        return product_quantities[supplier.pk][product.pk]

    order = create_empty_order(shop=shop)
    order.full_clean()
    order.save()

    for supplier, product_data in six.iteritems(product_quantities):
        for product, quantity in six.iteritems(product_data):
            add_product_to_order(order, supplier, product, quantity, 5)

    # Lines without quantity shouldn't affect refunds
    other_line = OrderLine(
        order=order, type=OrderLineType.OTHER, text="This random line for textual information", quantity=0
    )
    other_line.save()
    order.lines.add(other_line)

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
        order.create_refund(
            [{"line": "amount", "quantity": 1, "amount": order.shop.create_price(60)}], supplier=supplier1
        )

    # Supplier 1 refunds the order
    order.create_refund(_get_refund_data(order, supplier1))
    assert order.get_total_refunded_amount(supplier1).value == Decimal("55")  # 11 * 5
    assert order.get_total_unrefunded_amount(supplier1).value == Decimal("0")

    assert not order.can_create_refund(supplier1)
    assert order.can_create_refund()
    assert order.can_create_refund(supplier2)
    assert order.can_create_refund(supplier3)

    assert order.get_total_unrefunded_amount(supplier2).value == Decimal("80")  # 16 * 5
    assert order.get_total_unrefunded_quantity(supplier2) == Decimal("16")  # 3 x product1 and 13 x product2

    with pytest.raises(RefundExceedsAmountException):
        order.create_refund(
            [{"line": "amount", "quantity": 1, "amount": order.shop.create_price(81)}], supplier=supplier2
        )

    # Supplier 2 refunds the order
    order.create_refund(_get_refund_data(order, supplier2))
    assert order.get_total_refunded_amount(supplier2).value == Decimal("80")  # 11 * 5
    assert order.get_total_unrefunded_amount(supplier2).value == Decimal("0")
    assert not order.can_create_refund(supplier1)
    assert not order.can_create_refund(supplier2)
    assert order.can_create_refund()
    assert order.can_create_refund(supplier3)

    assert order.get_total_unrefunded_amount(supplier3).value == Decimal("255")  # 51 * 5
    assert order.get_total_unrefunded_quantity(supplier3) == Decimal("51")  # 3 x product1 and 13 x product2

    with override_settings(SHUUP_ALLOW_ARBITRARY_REFUNDS=False):
        with pytest.raises(RefundArbitraryRefundsNotAllowedException):
            order.create_refund(
                [{"line": "amount", "quantity": 1, "amount": order.shop.create_price(200)}], supplier=supplier3
            )

    order.create_refund([{"line": "amount", "quantity": 1, "amount": order.shop.create_price(200)}], supplier=supplier3)
    assert OrderLine.objects.filter(order=order, supplier=supplier3, type=OrderLineType.REFUND).exists()

    # Supplier 3 refunds the order
    order.create_refund(_get_refund_data(order, supplier3))
    assert order.get_total_refunded_amount(supplier3).value == Decimal("255")  # 11 * 5
    assert order.get_total_unrefunded_amount(supplier3).value == Decimal("0")
    assert not order.can_create_refund(supplier1)
    assert not order.can_create_refund(supplier2)
    assert not order.can_create_refund(supplier3)
    assert not order.can_create_refund()


@pytest.mark.django_db
def test_order_arbitrary_refunds_with_multiple_suppliers():
    shop = get_default_shop()
    supplier1 = get_supplier("simple_supplier", identifier="1", name="supplier1", shop=shop)
    supplier2 = get_supplier("simple_supplier", identifier="2", name="supplier2", shop=shop)
    supplier3 = get_supplier("simple_supplier", identifier="3", name="supplier3", shop=shop)

    product1 = create_product("sku1", shop=shop, default_price=10)
    shop_product1 = product1.get_shop_instance(shop=shop)
    shop_product1.suppliers.set([supplier1, supplier2, supplier3])

    product2 = create_product("sku2", shop=shop, default_price=10)
    shop_product2 = product1.get_shop_instance(shop=shop)
    shop_product2.suppliers.set([supplier1, supplier2])

    product3 = create_product("sku3", shop=shop, default_price=10, shipping_mode=ShippingMode.NOT_SHIPPED)
    shop_product3 = product1.get_shop_instance(shop=shop)
    shop_product3.suppliers.set([supplier3])

    product_quantities = {
        supplier1: {product1: 5, product2: 6},
        supplier2: {product1: 3, product2: 13},
        supplier3: {product1: 1, product3: 50},
    }

    def get_quantity(supplier, product):
        return product_quantities[supplier.pk][product.pk]

    order = create_empty_order(shop=shop)
    order.full_clean()
    order.save()

    for supplier, product_data in six.iteritems(product_quantities):
        for product, quantity in six.iteritems(product_data):
            add_product_to_order(order, supplier, product, quantity, 5)

    # Lines without quantity shouldn't affect refunds
    other_line = OrderLine(
        order=order, type=OrderLineType.OTHER, text="This random line for textual information", quantity=0
    )
    other_line.save()
    order.lines.add(other_line)

    order.cache_prices()
    order.create_payment(order.taxful_total_price)
    assert order.is_paid()

    # All supplier should be able to refund the order
    assert order.can_create_refund()
    assert order.can_create_refund(supplier1)
    assert order.can_create_refund(supplier2)
    assert order.can_create_refund(supplier3)

    # Step by step refund lines for supplier1
    assert order.can_create_refund()
    assert order.get_total_unrefunded_amount(supplier1).value == Decimal("55")  # 11 * 5
    assert order.get_total_unrefunded_amount().value == Decimal("390")  # 55 + 80 + 255
    proudct1_line_for_supplier1 = order.lines.filter(supplier=supplier1, product=product1).first()
    supplier1_refund_data = [
        {
            "line": proudct1_line_for_supplier1,
            "quantity": proudct1_line_for_supplier1.quantity,
            "amount": order.shop.create_price(20).amount,  # Line total is 5 * 5 = 25
            "restock_products": True,
        }
    ]
    order.create_refund(supplier1_refund_data)
    assert order.get_total_unrefunded_amount(supplier1).value == Decimal("35")

    order.create_refund(
        [{"line": "amount", "quantity": 1, "amount": order.shop.create_price(30).amount}], supplier=supplier1
    )

    assert order.get_total_unrefunded_amount(supplier1).value == Decimal("5")

    order.create_refund(
        [{"line": "amount", "quantity": 1, "amount": order.shop.create_price(5).amount}], supplier=supplier1
    )

    assert order.get_total_unrefunded_amount(supplier1).value == Decimal("0")
    assert order.can_create_refund(supplier1)  # Some quantity still left to refund

    proudct2_line_for_supplier1 = order.lines.filter(supplier=supplier1, product=product2).first()
    supplier1_restock_refund_data = [
        {
            "line": proudct2_line_for_supplier1,
            "quantity": proudct2_line_for_supplier1.quantity,
            "amount": order.shop.create_price(0).amount,  # Line total is 5 * 5 = 25
            "restock_products": True,
        }
    ]
    order.create_refund(supplier1_restock_refund_data)
    assert not order.can_create_refund(supplier1)

    # Step by step refund lines for supplier2
    assert order.can_create_refund()
    assert order.get_total_unrefunded_amount(supplier2).value == Decimal("80")  # 16 * 5
    assert order.get_total_unrefunded_amount().value == Decimal("335")  # 80 + 255
    proudct2_line_for_supplier2 = order.lines.filter(supplier=supplier2, product=product2).first()
    supplier2_refund_data = [
        {
            "line": proudct2_line_for_supplier2,
            "quantity": 10,
            "amount": order.shop.create_price(50).amount,  # Line total is 13 * 5 = 65
            "restock_products": True,
        }
    ]
    order.create_refund(supplier2_refund_data)
    assert order.get_total_unrefunded_amount(supplier2).value == Decimal("30")

    order.create_refund(
        [{"line": "amount", "quantity": 1, "amount": order.shop.create_price(5).amount}], supplier=supplier2
    )

    assert order.get_total_unrefunded_amount(supplier2).value == Decimal("25")

    order.create_refund(
        [{"line": "amount", "quantity": 1, "amount": order.shop.create_price(25).amount}], supplier=supplier2
    )

    assert order.get_total_unrefunded_amount(supplier2).value == Decimal("0")
    assert order.can_create_refund(supplier2)  # Some quantity still left to refund

    supplier2_restock_refund_data = [
        {
            "line": proudct2_line_for_supplier2,
            "quantity": 3,
            "amount": order.shop.create_price(0).amount,  # Line total is 5 * 5 = 25
            "restock_products": True,
        }
    ]
    order.create_refund(supplier2_restock_refund_data)

    proudct1_line_for_supplier2 = order.lines.filter(supplier=supplier2, product=product1).first()
    supplier1_restock_refund_data = [
        {
            "line": proudct1_line_for_supplier2,
            "quantity": proudct1_line_for_supplier2.quantity,
            "amount": order.shop.create_price(0).amount,  # Line total is 5 * 5 = 25
            "restock_products": True,
        }
    ]
    order.create_refund(supplier1_restock_refund_data)
    assert not order.can_create_refund(supplier2)

    # Step by step refund lines for supplier3
    assert order.can_create_refund()
    assert order.get_total_unrefunded_amount(supplier3).value == Decimal("255")  # 51 * 5
    assert order.get_total_unrefunded_amount().value == Decimal("255")  # 255

    order.create_refund(
        [{"line": "amount", "quantity": 1, "amount": order.shop.create_price(55).amount}], supplier=supplier3
    )

    assert order.get_total_unrefunded_amount(supplier3).value == Decimal("200")

    proudct3_line_for_supplier3 = order.lines.filter(supplier=supplier3, product=product3).first()
    supplier3_refund_data = [
        {
            "line": proudct3_line_for_supplier3,
            "quantity": 50,
            "amount": order.shop.create_price(200).amount,  # Line total is 13 * 5 = 65
            "restock_products": True,
        }
    ]
    order.create_refund(supplier3_refund_data)
    assert order.get_total_unrefunded_amount(supplier2).value == Decimal("0")
    assert order.get_total_unrefunded_amount().value == Decimal("0")
    assert order.can_create_refund(supplier3)  # Some quantity still left to refund

    proudct1_line_for_supplier3 = order.lines.filter(supplier=supplier3, product=product1).first()
    supplier3_restock_refund_data = [
        {
            "line": proudct1_line_for_supplier3,
            "quantity": proudct1_line_for_supplier3.quantity,
            "amount": order.shop.create_price(0).amount,  # Line total is 5 * 5 = 25
            "restock_products": True,
        }
    ]
    order.create_refund(supplier3_restock_refund_data)
    assert not order.can_create_refund(supplier3)
    assert not order.can_create_refund()


@pytest.mark.django_db
def test_order_refunds_with_other_lines():
    shop = get_default_shop()
    supplier = Supplier.objects.create(identifier="1", name="supplier1")
    supplier.shops.add(shop)

    product = create_product("sku", shop=shop, default_price=10)
    shop_product = product.get_shop_instance(shop=shop)
    shop_product.suppliers.set([supplier])

    order = create_empty_order(shop=shop)
    order.full_clean()
    order.save()

    add_product_to_order(order, supplier, product, 4, 5)

    # Lines without quantity shouldn't affect refunds
    other_line = OrderLine(
        order=order, type=OrderLineType.OTHER, text="This random line for textual information", quantity=0
    )
    other_line.save()
    order.lines.add(other_line)

    # Lines with quantity again should be able to be refunded normally.
    other_line_with_quantity = OrderLine(
        order=order, type=OrderLineType.OTHER, text="Special service 100$/h", quantity=1, base_unit_price_value=100
    )
    other_line_with_quantity.save()
    order.lines.add(other_line_with_quantity)

    assert other_line_with_quantity.max_refundable_quantity == 1
    assert other_line_with_quantity.max_refundable_amount.value == 100

    order.cache_prices()
    order.create_payment(order.taxful_total_price)
    assert order.is_paid()
    assert order.taxful_total_price_value == 120  # 100 + 4 * 20

    order.create_full_refund()
    assert order.taxful_total_price_value == 0


def _get_refund_data(order, supplier):
    return [
        {"line": line, "quantity": line.quantity, "amount": line.taxful_price.amount, "restock_products": True}
        for line in order.lines.filter(supplier=supplier)
    ]
