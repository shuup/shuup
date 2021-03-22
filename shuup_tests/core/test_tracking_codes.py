# -*- coding: utf-8 -*-
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
    create_order_with_product,
    create_product,
    get_default_product,
    get_default_supplier,
)


@pytest.mark.django_db
def test_tracking_codes():
    product = get_default_product()
    supplier = get_default_supplier()
    order = create_order_with_product(
        product, supplier=supplier, quantity=1, taxless_base_unit_price=10, tax_rate=decimal.Decimal("0.5")
    )
    _add_product_to_order(order, "duck-tape-1", 3, order.shop, supplier)
    _add_product_to_order(order, "water-1", 2, order.shop, supplier)

    order.cache_prices()
    order.check_all_verified()
    order.save()

    # Create shipment with tracking code for every product line.
    product_lines = order.lines.exclude(product_id=None)
    assert len(product_lines) == 3
    for line in product_lines:
        shipment = order.create_shipment({line.product: line.quantity}, supplier=supplier)
        if line.quantity != 3:
            shipment.tracking_code = "123FI"
            shipment.save()

    tracking_codes = order.get_tracking_codes()
    code_count = len(product_lines) - 1  # We skipped that one
    assert len(tracking_codes) == code_count
    assert len([tracking_code for tracking_code in tracking_codes if tracking_code == "123FI"]) == code_count


def _add_product_to_order(order, sku, quantity, shop, supplier):
    product = create_product(
        sku=sku,
        shop=shop,
        supplier=supplier,
        default_price=3.33,
    )
    add_product_to_order(order, supplier, product, quantity=quantity, taxless_base_unit_price=1)
