# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import decimal
import pytest
from django.conf import settings

from shuup.core.excs import NoProductsToShipException
from shuup.core.models import Shipment, ShipmentProduct, ShipmentStatus, ShippingMode, ShippingStatus
from shuup.testing.factories import (
    add_product_to_order,
    create_empty_order,
    create_product,
    get_default_shop,
    get_default_supplier,
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
    order.shipments.update(status=ShipmentStatus.SENT)
    order.update_shipping_status()
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
    order.shipments.update(status=ShipmentStatus.SENT)
    order.update_shipping_status()
    assert order.shipping_status == ShippingStatus.PARTIALLY_SHIPPED
    assert not order.can_edit()


@pytest.mark.django_db
def test_shipment_delete():
    shop = get_default_shop()
    supplier = get_default_supplier()
    order = _get_order(shop, supplier)
    assert order.can_edit()
    first_product_line = order.lines.exclude(product_id=None).first()
    assert first_product_line.quantity > 1
    shipment = order.create_shipment({first_product_line.product: 1}, supplier=supplier)
    order.shipments.update(status=ShipmentStatus.SENT)
    order.update_shipping_status()
    assert order.shipping_status == ShippingStatus.PARTIALLY_SHIPPED
    assert order.shipments.all().count() == 1

    # Test shipment delete
    shipment.soft_delete()
    assert order.shipments.all().count() == 1
    assert order.shipments.all_except_deleted().count() == 0
    # Check the shipping status update
    assert order.shipping_status == ShippingStatus.NOT_SHIPPED


@pytest.mark.django_db
@pytest.mark.parametrize("stock_managed", [True, False])
def test_shipment_with_insufficient_stock(stock_managed):
    if "shuup.simple_supplier" not in settings.INSTALLED_APPS:
        pytest.skip("Need shuup.simple_supplier in INSTALLED_APPS")

    from shuup_tests.simple_supplier.utils import get_simple_supplier

    shop = get_default_shop()
    supplier = get_simple_supplier(stock_managed=stock_managed)

    order = _get_order(shop, supplier, stocked=True)
    product_line = order.lines.products().first()
    product = product_line.product
    assert product_line.quantity == 15

    supplier.adjust_stock(product.pk, delta=10)
    stock_status = supplier.get_stock_status(product.pk)
    assert stock_status.physical_count == 10

    order.create_shipment({product: 5}, supplier=supplier)

    # mark all shipments as sent
    order.shipments.update(status=ShipmentStatus.SENT)
    order.update_shipping_status()

    assert order.shipping_status == ShippingStatus.PARTIALLY_SHIPPED
    assert order.shipments.all().count() == 1

    if stock_managed:
        # Stock error should be only raised for stock managed supplier
        supplier.stock_managed = True
        supplier.save()

        with pytest.raises(NoProductsToShipException):
            order.create_shipment({product: 10}, supplier=supplier)

        # Should be fine after adding more stock
        supplier.adjust_stock(product.pk, delta=5)

    order.create_shipment({product: 10}, supplier=supplier)


@pytest.mark.django_db
def test_shipment_with_unshippable_products():
    shop = get_default_shop()
    supplier = get_default_supplier()

    product = create_product("unshippable", shop=shop, supplier=supplier, default_price=5.55)
    product.shipping_mode = ShippingMode.NOT_SHIPPED
    product.save()
    order = _get_order(shop, supplier, stocked=False)
    initial_product_line_count = order.lines.products().count()
    add_product_to_order(order, supplier, product, quantity=4, taxless_base_unit_price=3)
    order.cache_prices()
    order.check_all_verified()
    order.save()

    assert order.shipments.count() == 0
    assert order.can_create_shipment()
    assert not order.can_set_complete()
    order.create_shipment_of_all_products(supplier=supplier)
    assert order.lines.products().count() == initial_product_line_count + 1

    assert order.shipments.count() == 1
    assert ShipmentProduct.objects.filter(shipment__order_id=order.id).count() == initial_product_line_count

    # mark all shipments as sent
    order.shipments.update(status=ShipmentStatus.SENT)
    order.update_shipping_status()

    assert order.shipping_status == ShippingStatus.FULLY_SHIPPED
    assert order.can_set_complete()


@pytest.mark.django_db
def test_order_with_only_unshippable_products():
    shop = get_default_shop()
    supplier = get_default_supplier()

    order = create_empty_order(shop=shop)
    order.full_clean()
    order.save()

    product = create_product("unshippable", shop=shop, supplier=supplier, default_price=5.55)
    product.shipping_mode = ShippingMode.NOT_SHIPPED
    product.save()
    add_product_to_order(order, supplier, product, quantity=4, taxless_base_unit_price=3)
    order.cache_prices()
    order.check_all_verified()
    order.save()

    assert not order.can_create_shipment()
    assert order.can_set_complete()


def _get_order(shop, supplier, stocked=False):
    order = create_empty_order(shop=shop)
    order.full_clean()
    order.save()
    for product_data in _get_product_data(stocked):
        quantity = product_data.pop("quantity")
        product = create_product(
            sku=product_data.pop("sku"), shop=shop, supplier=supplier, default_price=3.33, **product_data
        )
        add_product_to_order(order, supplier, product, quantity=quantity, taxless_base_unit_price=1)
    order.cache_prices()
    order.check_all_verified()
    order.save()
    return order


def _get_product_data(stocked=False):
    return [
        {
            "sku": "sku1234",
            "net_weight": decimal.Decimal("1"),
            "gross_weight": decimal.Decimal("43.34257"),
            "quantity": decimal.Decimal("15"),
        }
    ]
