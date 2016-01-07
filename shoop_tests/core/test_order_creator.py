# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import pytest

from shoop.core.models import get_person_contact, Order, OrderLineType, Shop
from shoop.core.order_creator import OrderCreator, OrderSource, SourceLine
from shoop.testing.factories import (
    get_address, get_default_payment_method, get_default_product,
    get_default_shipping_method, get_default_shop, get_default_supplier,
    get_initial_order_status
)
from shoop.testing.utils import apply_request_middleware
from shoop.utils.models import get_data_dict
from shoop_tests.utils.basketish_order_source import BasketishOrderSource


def test_invalid_order_source_updating():
    with pytest.raises(ValueError):  # Test nonexisting key updating
        OrderSource(Shop()).update(__totes_not_here__=True)


def test_invalid_source_line_updating():
    source = OrderSource(Shop())
    with pytest.raises(TypeError):  # Test forbidden keys
        SourceLine(source).update({"update": True})


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

    request = apply_request_middleware(rf.get("/"))

    creator = OrderCreator(request)
    order = creator.create_order(source)
    assert get_data_dict(source.billing_address) == get_data_dict(order.billing_address)
    assert get_data_dict(source.shipping_address) == get_data_dict(order.shipping_address)
    assert source.customer == order.customer
    assert source.payment_method == order.payment_method
    assert source.shipping_method == order.shipping_method
    assert order.pk

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

    request = apply_request_middleware(rf.get("/"))

    creator = OrderCreator(request)
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
    request = apply_request_middleware(rf.get("/"))

    creator = OrderCreator(request)
    order = Order.objects.get(pk=creator.create_order(source).pk)
    kid_line = order.lines.filter(sku="KIDKIDKID").first()
    assert kid_line
    assert kid_line.parent_line.product_id == product.pk
