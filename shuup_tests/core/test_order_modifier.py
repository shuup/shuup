# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.core.exceptions import ValidationError

from shuup.core.models import MutableAddress, Order, OrderLineType, Shop, ShopStatus, get_person_contact
from shuup.core.order_creator import OrderCreator
from shuup.core.order_creator._modifier import OrderModifier
from shuup.testing.factories import (
    create_package_product,
    get_default_payment_method,
    get_default_product,
    get_default_shipping_method,
    get_default_shop,
    get_default_supplier,
    get_initial_order_status,
)
from shuup_tests.utils.basketish_order_source import BasketishOrderSource


def get_order_and_source(admin_user, product):
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
        product=product,
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

    order, source = get_order_and_source(admin_user, get_default_product())

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
    order, source = get_order_and_source(admin_user, get_default_product())

    shop = Shop.objects.create(
        name="Another shop", identifier="another-shop", status=ShopStatus.ENABLED, public_name="Another shop"
    )

    source.shop = shop

    modifier = OrderModifier()

    assert order.shop != source.shop
    order_count = Order.objects.count()
    with pytest.raises(ValidationError):
        # Changing shop should be blocked. Source shop is just ignored.
        modifier.update_order_from_source(source, order)
    assert order_count == Order.objects.count(), "no new orders created"


def test_order_cannot_be_created():
    modifier = OrderModifier()
    with pytest.raises(AttributeError):
        modifier.create_order(None)


@pytest.mark.django_db
def test_modify_order_with_package_product(admin_user):
    package_children = 4
    package = create_package_product("parent", get_default_shop(), get_default_supplier(), 100, package_children)
    order, source = get_order_and_source(admin_user, package)
    source.add_line(
        type=OrderLineType.OTHER,
        quantity=1,
        base_unit_price=source.create_price(10),
        require_verification=True,
    )
    modifier = OrderModifier()
    modifier.update_order_from_source(source, order)
    assert order.lines.products().count() == 1 + package_children  # parent + children
    assert order.lines.other().count() == 2  # one added here + one from original order
