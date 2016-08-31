# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError

from shuup.core.models import (
    get_person_contact, Order, OrderLineType, Shop, StockBehavior
)
from shuup.core.order_creator import OrderCreator, OrderSource, SourceLine
from shuup.testing.factories import (
    create_package_product, get_address, get_default_payment_method,
    get_default_product, get_default_shipping_method, get_default_shop,
    get_default_supplier, get_initial_order_status
)
from shuup.utils.models import get_data_dict
from shuup_tests.utils.basketish_order_source import BasketishOrderSource


def test_invalid_order_source_updating():
    with pytest.raises(ValueError):  # Test nonexisting key updating
        OrderSource(Shop()).update(__totes_not_here__=True)


def test_invalid_source_line_updating():
    source = OrderSource(Shop())
    with pytest.raises(TypeError):  # Test forbidden keys
        SourceLine(source).update({"update": True})


def test_codes_type_conversion():
    source = OrderSource(Shop())

    assert source.codes == []

    source.add_code("t")
    source.add_code("e")
    source.add_code("s")
    assert source.codes == ["t", "e", "s"]

    was_added = source.add_code("t")
    assert was_added is False
    assert source.codes == ["t", "e", "s"]

    was_cleared = source.clear_codes()
    assert was_cleared
    assert source.codes == []
    was_cleared = source.clear_codes()
    assert not was_cleared

    source.add_code("test")
    source.add_code(1)
    source.add_code("1")
    assert source.codes == ["test", "1"]


def seed_source(user):
    source = BasketishOrderSource(get_default_shop())
    billing_address = get_address()
    shipping_address = get_address(name="Shippy Doge")
    source.status = get_initial_order_status()
    source.billing_address = billing_address
    source.shipping_address = shipping_address
    source.customer = get_person_contact(user)
    source.payment_method = get_default_payment_method()
    source.shipping_method = get_default_shipping_method()
    assert source.payment_method_id == get_default_payment_method().id
    assert source.shipping_method_id == get_default_shipping_method().id
    return source


@pytest.mark.django_db
def test_order_creator(rf, admin_user):
    source = seed_source(admin_user)
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        supplier=get_default_supplier(),
        quantity=1,
        base_unit_price=source.create_price(10),
    )
    source.add_line(
        type=OrderLineType.OTHER,
        quantity=1,
        base_unit_price=source.create_price(10),
        require_verification=True,
    )

    creator = OrderCreator()
    order = creator.create_order(source)
    assert get_data_dict(source.billing_address) == get_data_dict(order.billing_address)
    assert get_data_dict(source.shipping_address) == get_data_dict(order.shipping_address)
    assert source.customer == order.customer
    assert source.payment_method == order.payment_method
    assert source.shipping_method == order.shipping_method
    assert order.pk


@pytest.mark.django_db
def test_order_creator_with_package_product(rf, admin_user):
    if "shuup.simple_supplier" not in settings.INSTALLED_APPS:
        pytest.skip("Need shuup.simple_supplier in INSTALLED_APPS")
    from shuup_tests.simple_supplier.utils import get_simple_supplier

    shop = get_default_shop()
    supplier = get_simple_supplier()
    package_product = create_package_product("Package-Product-Test", shop=shop, supplier=supplier,
                                             children=2)
    shop_product =  package_product.get_shop_instance(shop)
    quantity_map = package_product.get_package_child_to_quantity_map()
    product_1, product_2 = quantity_map.keys()
    product_1.stock_behavior = StockBehavior.STOCKED
    product_1.save()
    product_2.stock_behavior = StockBehavior.STOCKED
    product_2.save()

    assert quantity_map[product_1] == 1
    assert quantity_map[product_2] == 2

    supplier.adjust_stock(product_1.pk, 1)
    supplier.adjust_stock(product_2.pk, 2)

    assert supplier.get_stock_status(product_1.pk).logical_count == 1
    assert supplier.get_stock_status(product_2.pk).logical_count == 2

    creator = OrderCreator()

    # There should be no exception when creating order with only package product
    source = seed_source(admin_user)
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=package_product,
        supplier=supplier,
        quantity=1,
        base_unit_price=source.create_price(10),
    )
    order = creator.create_order(source)

    # However, there should not be enough stock for both package and child products
    source = seed_source(admin_user)
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=package_product,
        supplier=supplier,
        quantity=1,
        base_unit_price=source.create_price(10),
    )
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=product_1,
        supplier=supplier,
        quantity=1,
        base_unit_price=source.create_price(10),
    )

    # And a validation error should be raised
    with pytest.raises(ValidationError):
        order = creator.create_order(source)


@pytest.mark.django_db
def test_order_creator_supplierless_product_line_conversion_should_fail(rf, admin_user):
    source = seed_source(admin_user)
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        supplier=None,
        quantity=1,
        base_unit_price=source.create_price(10),
    )

    creator = OrderCreator()
    with pytest.raises(ValueError):
        order = creator.create_order(source)


@pytest.mark.django_db
def test_order_source_parentage(rf, admin_user):
    source = seed_source(admin_user)
    product = get_default_product()
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=product,
        supplier=get_default_supplier(),
        quantity=1,
        base_unit_price=source.create_price(10),
        line_id="parent"
    )
    source.add_line(
        type=OrderLineType.OTHER,
        text="Child Line",
        sku="KIDKIDKID",
        quantity=1,
        base_unit_price=source.create_price(5),
        parent_line_id="parent"
    )

    creator = OrderCreator()
    order = Order.objects.get(pk=creator.create_order(source).pk)
    kid_line = order.lines.filter(sku="KIDKIDKID").first()
    assert kid_line
    assert kid_line.parent_line.product_id == product.pk
