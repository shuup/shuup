# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import decimal
import pytest

from shuup.testing.factories import (
    add_product_to_order,
    create_empty_order,
    create_product,
    get_default_shop,
    get_default_supplier,
)


@pytest.mark.django_db
def test_shipment_weights_separate_shipments():
    shop = get_default_shop()
    supplier = get_default_supplier()
    order = _get_order(shop, supplier)
    product_lines = order.lines.exclude(product_id=None)
    for line in product_lines:
        shipment = order.create_shipment({line.product: line.quantity}, supplier=supplier)
        assert shipment.weight == line.quantity * line.product.gross_weight


@pytest.mark.django_db
def test_shipment_weights_ship_all():
    shop = get_default_shop()
    supplier = get_default_supplier()
    order = _get_order(shop, supplier)
    shipment = order.create_shipment_of_all_products(supplier=supplier)
    assert shipment.weight == sum([_get_weight_from_product_data(product_data) for product_data in _get_product_data()])


def _get_weight_from_product_data(product_data):
    return product_data["quantity"] * product_data["gross_weight"]


def _get_order(shop, supplier):
    order = create_empty_order(shop=shop)
    order.full_clean()
    order.save()
    for product_data in _get_product_data():
        quantity = product_data.pop("quantity")
        product = create_product(
            sku=product_data.pop("sku"), shop=shop, supplier=supplier, default_price=3.33, **product_data
        )
        add_product_to_order(order, supplier, product, quantity=quantity, taxless_base_unit_price=1)
    order.cache_prices()
    order.check_all_verified()
    order.save()
    return order


def _get_product_data():
    return [
        {
            "sku": "sku1234",
            "net_weight": decimal.Decimal("1"),
            "gross_weight": decimal.Decimal("43.34257"),
            "quantity": decimal.Decimal("43"),
        },
        {
            "sku": "sku4321",
            "net_weight": decimal.Decimal("11.342569"),
            "gross_weight": decimal.Decimal("11.34257"),
            "quantity": decimal.Decimal("1.3245"),
        },
        {
            "sku": "sku1111",
            "net_weight": decimal.Decimal("0.00"),
            "gross_weight": decimal.Decimal("0.00"),
            "quantity": decimal.Decimal("100"),
        },
    ]
