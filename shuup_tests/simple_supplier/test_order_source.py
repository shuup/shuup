# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.core.models import OrderLineType, get_person_contact
from shuup.testing.factories import (
    create_product,
    get_default_payment_method,
    get_default_shipping_method,
    get_default_shop,
    get_initial_order_status,
)
from shuup_tests.core.test_order_creator import seed_source
from shuup_tests.simple_supplier.utils import get_simple_supplier
from shuup_tests.utils.basketish_order_source import BasketishOrderSource


def seed_source(user, shop):
    source = BasketishOrderSource(shop)
    source.status = get_initial_order_status()
    source.customer = get_person_contact(user)
    source.payment_method = get_default_payment_method()
    source.shipping_method = get_default_shipping_method()
    return source


@pytest.mark.django_db
def test_order_source(rf, admin_user):
    """
    Test order source validation with stocked products.
    """
    shop = get_default_shop()
    supplier = get_simple_supplier()
    product = create_product("simple-test-product", shop, supplier)
    quantity = 345
    supplier.adjust_stock(product.pk, quantity)
    assert supplier.get_stock_statuses([product.id])[product.id].logical_count == quantity
    assert not list(supplier.get_orderability_errors(product.get_shop_instance(shop), quantity, customer=None))
    assert list(supplier.get_orderability_errors(product.get_shop_instance(shop), quantity + 1, customer=None))

    source = seed_source(admin_user, shop)
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=product,
        supplier=supplier,
        quantity=quantity,
        base_unit_price=source.create_price(10),
    )
    assert not list(source.get_validation_errors())

    source.add_line(
        type=OrderLineType.PRODUCT,
        product=product,
        supplier=supplier,
        quantity=quantity,
        base_unit_price=source.create_price(10),
    )
    assert list(source.get_validation_errors())
