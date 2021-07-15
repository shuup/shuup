# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import decimal
import pytest

from shuup.admin.modules.orders.views import OrderSetPaidView
from shuup.core.models import Order, PaymentStatus
from shuup.testing.factories import (
    add_product_to_order,
    create_empty_order,
    create_product,
    get_default_shop,
    get_default_supplier,
)
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
@pytest.mark.parametrize("has_price", (True, False))
def test_order_set_paid_action(rf, admin_user, has_price):
    shop = get_default_shop()
    supplier = get_default_supplier()
    order = _get_order(shop, supplier, has_price)
    view = OrderSetPaidView.as_view()
    request = apply_request_middleware(rf.post("/"), user=admin_user)
    response = view(request, pk=order.pk)
    order = Order.objects.get(id=order.id)  # Reload order object
    if has_price:
        assert order.payment_status == PaymentStatus.NOT_PAID
    else:
        assert order.payment_status == PaymentStatus.FULLY_PAID


@pytest.mark.django_db
@pytest.mark.parametrize("has_price", (True, False))
def test_deferred_order_set_paid_action(rf, admin_user, has_price):
    shop = get_default_shop()
    supplier = get_default_supplier()
    order = _get_order(shop, supplier, has_price)
    # set payment status to deferred
    order.payment_status = PaymentStatus.DEFERRED
    order.save()
    view = OrderSetPaidView.as_view()
    request = apply_request_middleware(rf.post("/"), user=admin_user)
    response = view(request, pk=order.pk)
    order = Order.objects.get(id=order.id)  # Reload order object
    if has_price:
        assert order.payment_status == PaymentStatus.DEFERRED
    else:
        assert order.payment_status == PaymentStatus.FULLY_PAID


def _get_order(shop, supplier, has_price):
    order = create_empty_order(shop=shop)
    order.full_clean()
    order.save()
    for product_data in _get_product_data(has_price):
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


def _get_product_data(has_price):
    return [
        {
            "sku": "sku1234",
            "default_price": decimal.Decimal("123" if has_price else "0"),
            "quantity": decimal.Decimal("1"),
            "tax_rate": decimal.Decimal("0.24"),
        },
        {
            "sku": "sku2345",
            "default_price": decimal.Decimal("15" if has_price else "0"),
            "quantity": decimal.Decimal("1"),
            "tax_rate": decimal.Decimal("0.24"),
        },
    ]
