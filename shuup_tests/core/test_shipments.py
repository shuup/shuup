# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import decimal
import pytest

from shuup.core.models import Shipment, ShippingStatus
from shuup.testing.factories import (
    add_product_to_order, create_empty_order, create_product,
    get_default_shop, get_default_supplier
)


@pytest.mark.django_db
def test_shipment_identifier():
    shop = get_default_shop()
    supplier = get_default_supplier()
    order = _get_order(shop, supplier)
    product_lines = order.lines.exclude(product_id=None)
    for line in product_lines:
        for i in range(0, int(line.quantity)):
            shipment = order.create_shipment({line.product: 1}, supplier=supplier)
            expected_key_start = "%s/%s" % (order.pk, i)
            assert shipment.identifier.startswith(expected_key_start)
        assert order.shipments.count() == int(line.quantity)
    assert order.shipping_status == ShippingStatus.FULLY_SHIPPED  # Check that order is now fully shipped
    assert not order.can_edit()

@pytest.mark.django_db
def test_shipment_creation_from_unsaved_shipment():
    shop = get_default_shop()
    supplier = get_default_supplier()
    order = _get_order(shop, supplier)
    product_lines = order.lines.exclude(product_id=None)
    for line in product_lines:
        for i in range(0, int(line.quantity)):
            unsaved_shipment = Shipment(order=order, supplier=supplier)
            shipment = order.create_shipment({line.product: 1}, shipment=unsaved_shipment)
            expected_key_start = "%s/%s" % (order.pk, i)
            assert shipment.identifier.startswith(expected_key_start)
        assert order.shipments.count() == int(line.quantity)


@pytest.mark.django_db
def test_shipment_creation_without_supplier_and_shipment():
    shop = get_default_shop()
    supplier = get_default_supplier()
    order = _get_order(shop, supplier)
    product_lines = order.lines.exclude(product_id=None)
    for line in product_lines:
        for i in range(0, int(line.quantity)):
            with pytest.raises(AssertionError):
                order.create_shipment({line.product: 1})
    assert order.shipments.count() == 0


@pytest.mark.django_db
def test_shipment_creation_with_invalid_unsaved_shipment():
    shop = get_default_shop()
    supplier = get_default_supplier()
    order = _get_order(shop, supplier)
    second_order = create_empty_order(shop=shop)
    second_order.full_clean()
    second_order.save()
    product_lines = order.lines.exclude(product_id=None)
    for line in product_lines:
        for i in range(0, int(line.quantity)):
            with pytest.raises(AssertionError):
                unsaved_shipment = Shipment(supplier=supplier, order=second_order)
                order.create_shipment({line.product: 1}, shipment=unsaved_shipment)
    assert order.shipments.count() == 0


@pytest.mark.django_db
def test_partially_shipped_order_status():
    shop = get_default_shop()
    supplier = get_default_supplier()
    order = _get_order(shop, supplier)
    assert order.can_edit()
    first_product_line = order.lines.exclude(product_id=None).first()
    assert first_product_line.quantity > 1
    order.create_shipment({first_product_line.product: 1}, supplier=supplier)
    assert order.shipping_status == ShippingStatus.PARTIALLY_SHIPPED
    assert not order.can_edit()


def _get_order(shop, supplier):
    order = create_empty_order(shop=shop)
    order.full_clean()
    order.save()
    for product_data in _get_product_data():
        quantity = product_data.pop("quantity")
        product = create_product(
            sku=product_data.pop("sku"),
            shop=shop,
            supplier=supplier,
            default_price=3.33,
            **product_data)
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
            "quantity": decimal.Decimal("15")
        }
    ]
