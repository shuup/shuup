# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.core.exceptions import ValidationError

from shuup.core.models import Order, MutableAddress, OrderLineType, get_person_contact, Shop, ShopStatus
from shuup.core.order_creator import OrderCreator
from shuup.core.order_creator._modifier import OrderModifier
from shuup.testing.factories import (
    get_initial_order_status, get_default_payment_method, get_default_shipping_method,
    get_default_shop, get_default_product, get_default_supplier
)
from shuup_tests.utils.basketish_order_source import BasketishOrderSource


def get_order_and_source(admin_user):
    # create original source to tamper with
    source = BasketishOrderSource(get_default_shop())
    source.status = get_initial_order_status()
    source.billing_address = MutableAddress.objects.create(name="Original Billing")
    source.shipping_address = MutableAddress.objects.create(name="Original Shipping")
    source.customer = get_person_contact(admin_user)
    source.payment_method = get_default_payment_method()
    source.shipping_method = get_default_shipping_method()
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
    assert len(source.get_lines()) == 2
    source.creator = admin_user
    creator = OrderCreator()
    order = creator.create_order(source)
    return order, source


@pytest.mark.django_db
def test_order_modifier(rf, admin_user):

    order, source = get_order_and_source(admin_user)

    # get original values
    taxful_total_price = order.taxful_total_price_value
    taxless_total_price = order.taxless_total_price_value
    original_line_count = order.lines.count()

    # modify source
    source.billing_address = MutableAddress.objects.create(name="New Billing")
    source.shipping_address = MutableAddress.objects.create(name="New Shipping")

    modifier = OrderModifier()
    modifier.update_order_from_source(source, order)  # new param to edit order from source

    assert Order.objects.count() == 1

    order = Order.objects.first()
    assert order.billing_address.name == "New Billing"
    assert order.shipping_address.name == "New Shipping"
    assert order.taxful_total_price_value == taxful_total_price
    assert order.taxless_total_price_value == taxless_total_price

    # add new line to order source
    source.add_line(
        type=OrderLineType.OTHER,
        quantity=1,
        base_unit_price=source.create_price(10),
        require_verification=True,
    )
    modifier.update_order_from_source(source, order)

    assert order.lines.count() == original_line_count + 1


@pytest.mark.django_db
def test_shop_change(rf, admin_user):
    order, source = get_order_and_source(admin_user)

    shop = Shop.objects.create(
        name="Another shop",
        identifier="another-shop",
        status=ShopStatus.ENABLED,
        public_name="Another shop"
    )

    source.shop = shop

    modifier = OrderModifier()
    assert order.shop != source.shop
    # Changing shop should be blocked. Source shop is just ignored.
    edited_order = modifier.update_order_from_source(source, order)
    assert edited_order.shop == order.shop


def test_order_cannot_be_created():
    modifier = OrderModifier()
    with pytest.raises(AttributeError):
        modifier.create_order(None)
