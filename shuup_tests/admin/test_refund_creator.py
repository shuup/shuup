# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import pytest

from shuup.admin.modules.orders.views.refund import (
    OrderCreateFullRefundView, OrderCreateRefundView
)
from shuup.core.models import OrderLineType
from shuup.testing.factories import (
    create_order_with_product, create_product, get_default_shop,
    get_default_supplier
)
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_create_refund_view(rf, admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(sku="test-sku", shop=shop, supplier=supplier, default_price=3.33)
    order = create_order_with_product(product, supplier, quantity=1, taxless_base_unit_price=1, shop=shop)
    order.cache_prices()
    order.save()

    assert not order.has_refunds()
    assert len(order.lines.all()) == 1

    product_line = order.lines.first()

    data = {
        "form-0-line_number": 0,
        "form-0-quantity": 1,
        "form-0-amount": 1,
        "form-0-restock_products": False,
        "form-INITIAL_FORMS": 0,
        "form-MAX_NUM_FORMS": 1000,
        "form-TOTAL_FORMS": 1,
        "form-MIN_NUM_FORMS": 0,
    }

    request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
    view = OrderCreateRefundView.as_view()
    response = view(request, pk=order.pk)
    assert response.status_code == 302
    assert order.has_refunds()

    assert len(order.lines.all()) == 2
    refund_line = order.lines.filter(type=OrderLineType.REFUND).last()
    assert refund_line
    assert refund_line.taxful_price == -product_line.taxful_price


@pytest.mark.django_db
def test_create_full_refund_view(rf, admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(sku="test-sku", shop=shop, supplier=supplier, default_price=3.33)
    order = create_order_with_product(product, supplier, quantity=1, taxless_base_unit_price=1, shop=shop)
    order.cache_prices()

    original_total_price = order.taxful_total_price

    assert not order.has_refunds()
    assert len(order.lines.all()) == 1
    assert order.taxful_total_price.amount.value != 0

    data = {
        "restock_products": "on",
    }

    request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
    view = OrderCreateFullRefundView.as_view()
    response = view(request, pk=order.pk)
    assert response.status_code == 302
    assert order.has_refunds()
    order.cache_prices()

    assert order.taxful_total_price.amount.value == 0
    refund_line = order.lines.filter(type=OrderLineType.REFUND).last()
    assert refund_line
    assert refund_line.taxful_price == -original_total_price
