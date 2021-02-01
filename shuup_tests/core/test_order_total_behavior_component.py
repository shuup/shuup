# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import decimal
import pytest

from shuup.core.models import (
    get_person_contact, OrderLineType, OrderTotalLimitBehaviorComponent
)
from shuup.testing.factories import (
    create_product, get_address, get_payment_method,
    get_shipping_method, get_default_supplier,
    get_initial_order_status, get_shop
)
from shuup_tests.utils.basketish_order_source import BasketishOrderSource


@pytest.mark.django_db
@pytest.mark.parametrize("min,max,price", [
    (None, "10.32", decimal.Decimal("0.01")),
    ("0", "10.32", decimal.Decimal("10.32")),
    ("0", "10.32", decimal.Decimal("0")),
    ("10.00", "50.00", decimal.Decimal("10.01")),
    ("32.45678", None, decimal.Decimal("53.57")),
    (None, None, decimal.Decimal("1000000"))
])
def test_order_total_behavior_available(admin_user, min, max, price):
    source, shipping_method = _get_source(admin_user, True, price)
    assert shipping_method.behavior_components.count() == 0
    component = OrderTotalLimitBehaviorComponent.objects.create(
        min_price_value=min, max_price_value=max)
    shipping_method.behavior_components.add(component)

    assert shipping_method.behavior_components.count() == 1
    unavailability_reasons = list(shipping_method.get_unavailability_reasons(source))
    assert len(unavailability_reasons) == 0
    shipping_method.behavior_components.clear()


@pytest.mark.django_db
@pytest.mark.parametrize("min,max,price", [
    (None, "10.32", decimal.Decimal("10.33")),
    ("10.00", "50.00", decimal.Decimal("5")),
    ("10.00", "50.00", decimal.Decimal("62")),
    ("32.45678", None, decimal.Decimal("20"))
])
def test_order_total_behavior_unavailable(admin_user, min, max, price):
    source, shipping_method = _get_source(admin_user, False, price)
    assert shipping_method.behavior_components.count() == 0
    component = OrderTotalLimitBehaviorComponent.objects.create(
        min_price_value=min, max_price_value=max)
    shipping_method.behavior_components.add(component)

    assert shipping_method.behavior_components.count() == 1
    unavailability_reasons = list(shipping_method.get_unavailability_reasons(source))
    assert len(unavailability_reasons) > 0
    shipping_method.behavior_components.clear()


def _get_source(user, prices_include_taxes, total_price_value):
    shop = get_shop(prices_include_taxes)
    payment_method = get_payment_method(shop)
    shipping_method = get_shipping_method(shop)
    source = _seed_source(shop, user)
    source.payment_method = payment_method
    source.shipping_method = shipping_method
    assert source.payment_method_id == payment_method.id
    assert source.shipping_method_id == shipping_method.id

    supplier = get_default_supplier()
    product = create_product(
        sku="test-%s--%s" % (prices_include_taxes, total_price_value),
        shop=source.shop,
        supplier=supplier,
        default_price=total_price_value
    )
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=product,
        supplier=supplier,
        quantity=1,
        base_unit_price=source.create_price(total_price_value),
    )
    if prices_include_taxes:
        assert source.taxful_total_price.value == total_price_value
    else:
        assert source.taxless_total_price.value == total_price_value
    assert payment_method == source.payment_method
    assert shipping_method == source.shipping_method
    return source, shipping_method


def _seed_source(shop, user):
    source = BasketishOrderSource(shop)
    billing_address = get_address()
    shipping_address = get_address(name="Test street")
    source.status = get_initial_order_status()
    source.billing_address = billing_address
    source.shipping_address = shipping_address
    source.customer = get_person_contact(user)
    return source
