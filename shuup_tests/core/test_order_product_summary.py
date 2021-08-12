# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.core.models import ShipmentStatus, ShippingMode, Supplier, SupplierModule
from shuup.testing.factories import add_product_to_order, create_empty_order, create_product, get_default_shop


@pytest.mark.django_db
def test_order_product_summary_with_multiple_suppliers():
    shop = get_default_shop()
    supplier1 = Supplier.objects.create(identifier="1", name="supplier1")
    supplier1.shops.add(shop)
    supplier1.supplier_modules.set(SupplierModule.objects.all())
    supplier2 = Supplier.objects.create(identifier="2")
    supplier2.shops.add(shop)
    supplier2.supplier_modules.set(SupplierModule.objects.all())
    supplier3 = Supplier.objects.create(identifier="3", name="s")
    supplier3.shops.add(shop)
    supplier3.supplier_modules.set(SupplierModule.objects.all())

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
        supplier1.pk: {product1.pk: 5, product2.pk: 6},
        supplier2.pk: {product1.pk: 3, product2.pk: 13},
        supplier3.pk: {product1.pk: 1, product3.pk: 50},
    }

    def get_quantity(supplier, product):
        return product_quantities[supplier.pk][product.pk]

    order = create_empty_order(shop=shop)
    order.full_clean()
    order.save()

    # Add product 3 to order for supplier 3
    add_product_to_order(order, supplier3, product3, get_quantity(supplier3, product3), 8)
    assert order.get_product_ids_and_quantities()[product3.pk] == 50
    assert not order.has_products_requiring_shipment()
    assert not order.has_products_requiring_shipment(supplier3)

    # Add product 2 to order for supplier 1
    add_product_to_order(order, supplier1, product2, get_quantity(supplier1, product2), 7)
    assert order.get_product_ids_and_quantities()[product2.pk] == 6
    assert order.has_products_requiring_shipment()
    assert order.has_products_requiring_shipment(supplier1)
    assert not order.has_products_requiring_shipment(supplier3)

    # Add product 2 to order for supplier 2
    add_product_to_order(order, supplier2, product2, get_quantity(supplier2, product2), 6)
    assert order.get_product_ids_and_quantities()[product2.pk] == 19
    assert order.has_products_requiring_shipment()
    assert order.has_products_requiring_shipment(supplier1)
    assert order.has_products_requiring_shipment(supplier2)
    assert not order.has_products_requiring_shipment(supplier3)

    # Add product 1 to order for supplier 3
    add_product_to_order(order, supplier3, product1, get_quantity(supplier3, product1), 5)
    assert order.get_product_ids_and_quantities()[product1.pk] == 1
    assert order.has_products_requiring_shipment()
    assert order.has_products_requiring_shipment(supplier1)
    assert order.has_products_requiring_shipment(supplier2)
    assert order.has_products_requiring_shipment(supplier3)

    # Add product 1 for supplier 1 and 3
    add_product_to_order(order, supplier1, product1, get_quantity(supplier1, product1), 4)
    add_product_to_order(order, supplier2, product1, get_quantity(supplier2, product1), 3)
    assert order.get_product_ids_and_quantities()[product1.pk] == 9

    product_summary = order.get_product_summary()
    _assert_product_summary(product_summary, product1.pk, 9, 9, 0, 0)
    _assert_product_summary(product_summary, product2.pk, 19, 19, 0, 0)
    _assert_product_summary(product_summary, product3.pk, 50, 0, 0, 0)

    # Test product summary per supplier
    product_summary = order.get_product_summary(supplier1)
    _assert_product_summary(product_summary, product1.pk, 5, 5, 0, 0)
    _assert_product_summary(product_summary, product2.pk, 6, 6, 0, 0)
    _assert_product_summary(product_summary, product3.pk, 0, 0, 0, 0)

    product_summary = order.get_product_summary(supplier2.pk)
    _assert_product_summary(product_summary, product1.pk, 3, 3, 0, 0)
    _assert_product_summary(product_summary, product2.pk, 13, 13, 0, 0)
    _assert_product_summary(product_summary, product3.pk, 0, 0, 0, 0)

    product_summary = order.get_product_summary(supplier3.pk)
    _assert_product_summary(product_summary, product1.pk, 1, 1, 0, 0)
    _assert_product_summary(product_summary, product2.pk, 0, 0, 0, 0)
    _assert_product_summary(product_summary, product3.pk, 50, 0, 0, 0)

    # Make order fully paid so we can start creting shipments and refunds
    order.cache_prices()
    order.check_all_verified()
    order.create_payment(order.taxful_total_price)
    assert order.is_paid()

    # Let's make sure all good with unshipped products
    unshipped_products = order.get_unshipped_products()
    assert unshipped_products[product1.pk]["unshipped"] == 9
    assert unshipped_products[product2.pk]["unshipped"] == 19
    assert unshipped_products.get(product3.pk) is None

    unshipped_products = order.get_unshipped_products(supplier1)
    assert unshipped_products[product1.pk]["unshipped"] == 5
    assert unshipped_products[product2.pk]["unshipped"] == 6

    unshipped_products = order.get_unshipped_products(supplier2)
    assert unshipped_products[product1.pk]["unshipped"] == 3
    assert unshipped_products[product2.pk]["unshipped"] == 13

    unshipped_products = order.get_unshipped_products(supplier3)
    assert unshipped_products[product1.pk]["unshipped"] == 1
    assert unshipped_products.get(product2.pk) is None
    assert unshipped_products.get(product3.pk) is None

    # Refund product3
    line_to_refund = order.lines.filter(product_id=product3.pk).first()
    order.create_refund([{"line": line_to_refund, "quantity": 10, "amount": shop.create_price("10").amount}])
    product_summary = order.get_product_summary()
    _assert_product_summary(product_summary, product3.pk, 50, 0, 0, 10)
    product_summary = order.get_product_summary(supplier3.pk)
    _assert_product_summary(product_summary, product3.pk, 50, 0, 0, 10)

    order.create_refund([{"line": line_to_refund, "quantity": 40, "amount": shop.create_price("20").amount}])
    product_summary = order.get_product_summary()
    _assert_product_summary(product_summary, product3.pk, 50, 0, 0, 50)
    product_summary = order.get_product_summary(supplier3.pk)
    _assert_product_summary(product_summary, product3.pk, 50, 0, 0, 50)

    # Then ship product 1 for all suppliers one by one
    order.create_shipment({product1: 1}, supplier=supplier3)
    unshipped_products = order.get_unshipped_products(supplier3)
    assert unshipped_products.get(product1.pk) is None
    unshipped_products = order.get_unshipped_products()
    assert unshipped_products[product1.pk]["unshipped"] == 8

    order.create_shipment({product1: 3}, supplier=supplier2)
    unshipped_products = order.get_unshipped_products(supplier2)
    assert unshipped_products.get(product1.pk) is None
    unshipped_products = order.get_unshipped_products()
    assert unshipped_products[product1.pk]["unshipped"] == 5

    order.create_shipment({product1: 5}, supplier=supplier1)
    unshipped_products = order.get_unshipped_products(supplier1)
    assert unshipped_products.get(product1.pk) is None
    unshipped_products = order.get_unshipped_products()
    assert unshipped_products.get(product1.pk) is None

    # Then ship product 2 for all suppliers with a twist
    order.create_shipment({product2: 13}, supplier=supplier2)
    unshipped_products = order.get_unshipped_products(supplier2)
    assert unshipped_products.get(product2.pk) is None
    unshipped_products = order.get_unshipped_products()
    assert unshipped_products[product2.pk]["unshipped"] == 6

    order.create_shipment({product2: 5}, supplier=supplier1)
    unshipped_products = order.get_unshipped_products(supplier1)
    assert unshipped_products[product2.pk]["unshipped"] == 1
    unshipped_products = order.get_unshipped_products()
    assert unshipped_products[product2.pk]["unshipped"] == 1
    product_summary = order.get_product_summary()
    _assert_product_summary(product_summary, product2.pk, 19, 1, 18, 0)

    # Refund the last product and see all falling in place
    line_to_refund = order.lines.filter(product_id=product2.pk, supplier=supplier1).first()
    order.create_refund([{"line": line_to_refund, "quantity": 1, "amount": shop.create_price("1").amount}])

    assert not order.get_unshipped_products()
    order.shipments.update(status=ShipmentStatus.SENT)
    order.update_shipping_status()
    assert order.is_fully_shipped()

    # Verify product summary
    product_summary = order.get_product_summary()
    _assert_product_summary(product_summary, product1.pk, 9, 0, 9, 0, suppliers=[supplier1, supplier2, supplier3])
    _assert_product_summary(product_summary, product2.pk, 19, 0, 18, 1, suppliers=[supplier1, supplier2])
    _assert_product_summary(product_summary, product3.pk, 50, 0, 0, 50, suppliers=[supplier3])

    # Order prodcuts and quantities still match, right?
    order_products_and_quantities = order.get_product_ids_and_quantities()
    assert order_products_and_quantities[product1.pk] == 9
    assert order_products_and_quantities[product2.pk] == 19
    assert order_products_and_quantities[product3.pk] == 50

    # Order still has products requiring shipments, right?
    assert order.has_products_requiring_shipment()
    assert order.has_products_requiring_shipment(supplier1)
    assert order.has_products_requiring_shipment(supplier2)
    assert order.has_products_requiring_shipment(supplier3)


def _assert_product_summary(product_summary, product_pk, ordered, unshipped, shipped, refunded, suppliers=None):
    assert product_summary[product_pk]["ordered"] == ordered
    assert product_summary[product_pk]["unshipped"] == unshipped
    assert product_summary[product_pk]["shipped"] == shipped
    assert product_summary[product_pk]["refunded"] == refunded

    if suppliers:
        for supplier in suppliers:
            assert supplier.name in product_summary[product_pk]["suppliers"]
