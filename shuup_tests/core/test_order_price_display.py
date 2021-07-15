# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import decimal
import pytest

from shuup.core.templatetags.shuup_common import money
from shuup.testing.factories import (
    add_product_to_order,
    create_empty_order,
    create_product,
    get_default_shop,
    get_default_supplier,
)


@pytest.mark.django_db
def test_order_price_display():
    shop = get_default_shop()
    supplier = get_default_supplier()
    order = _get_order(shop, supplier)

    # Formatted line prices should match with the formatted order total prices
    # Strip euro sign before converting formatted price to decimal
    taxful_total = decimal.Decimal("0.00")
    taxless_total = decimal.Decimal("0.00")
    for line in order.lines.all():
        taxful_total += decimal.Decimal(money(line.taxful_price).strip("\u20ac"))
        taxless_total += decimal.Decimal(money(line.taxless_price).strip("\u20ac"))
    assert decimal.Decimal(money(order.taxful_total_price).strip("\u20ac")) == taxful_total
    assert decimal.Decimal(money(order.taxless_total_price).strip("\u20ac")) == taxless_total


def _get_order(shop, supplier):
    order = create_empty_order(shop=shop)
    order.full_clean()
    order.save()
    for product_data in _get_product_data():
        quantity = product_data.pop("quantity")
        tax_rate = product_data.pop("tax_rate")
        product = create_product(sku=product_data.pop("sku"), shop=shop, supplier=supplier, **product_data)
        add_product_to_order(
            order,
            supplier,
            product,
            quantity=quantity,
            taxless_base_unit_price=product_data["default_price"],
            tax_rate=tax_rate,
        )
    order.cache_prices()
    order.check_all_verified()
    order.save()
    return order


def _get_product_data():
    return [
        {
            "sku": "sku1234",
            "default_price": decimal.Decimal("14.756"),
            "quantity": decimal.Decimal("1"),
            "tax_rate": decimal.Decimal("0.24"),
        },
        {
            "sku": "sku12345",
            "default_price": decimal.Decimal("10"),
            "quantity": decimal.Decimal("5"),
            "tax_rate": decimal.Decimal("0.24"),
        },
        {
            "sku": "sku123456",
            "default_price": decimal.Decimal("14.756"),
            "quantity": decimal.Decimal("2"),
            "tax_rate": decimal.Decimal("0.24"),
        },
        {
            "sku": "sku1234567",
            "default_price": decimal.Decimal("8.8164"),
            "quantity": decimal.Decimal("1"),
            "tax_rate": decimal.Decimal("0.14"),
        },
        {
            "sku": "sku12345678",
            "default_price": decimal.Decimal("17.6328"),
            "quantity": decimal.Decimal("4"),
            "tax_rate": decimal.Decimal("0.00"),
        },
    ]
