# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import pytest
from bs4 import BeautifulSoup
from django.test import override_settings

from shuup.admin.modules.orders.views.refund import OrderCreateFullRefundView, OrderCreateRefundView
from shuup.core.models import OrderLine, OrderLineType
from shuup.testing.factories import (
    add_product_to_order,
    create_empty_order,
    create_order_with_product,
    create_product,
    get_default_shop,
    get_default_supplier,
)
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import force_text


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
    supplier = get_default_supplier(shop)
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


@pytest.mark.django_db
def test_arbitrary_refund_availability(rf, admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(sku="test-sku", shop=shop, supplier=supplier, default_price=3.33)
    order = create_order_with_product(product, supplier, quantity=1, taxless_base_unit_price=1, shop=shop)
    order.cache_prices()
    order.save()

    assert not order.has_refunds()
    assert len(order.lines.all()) == 1

    def get_refund_view_content():
        request = apply_request_middleware(rf.get("/"), user=admin_user)
        view = OrderCreateRefundView.as_view()
        response = view(request, pk=order.pk)
        return force_text(response.render().content)

    refund_option_str = '<option value="amount">Refund arbitrary amount</option>'
    assert refund_option_str in get_refund_view_content()
    with override_settings(SHUUP_ALLOW_ARBITRARY_REFUNDS=False):
        assert refund_option_str not in get_refund_view_content()


@pytest.mark.django_db
def test_order_refunds_with_other_lines(rf, admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    supplier.shops.add(shop)

    product = create_product("sku", shop=shop, default_price=10)
    shop_product = product.get_shop_instance(shop=shop)
    shop_product.suppliers.set([supplier])

    order = create_empty_order(shop=shop)
    order.full_clean()
    order.save()

    add_product_to_order(order, supplier, product, 4, 5)

    # Lines without quantity shouldn't affect refunds
    other_line = OrderLine(
        order=order, type=OrderLineType.OTHER, text="This random line for textual information", quantity=0
    )
    other_line.save()
    order.lines.add(other_line)

    # Lines with quantity again should be able to be refunded normally.
    other_line_with_quantity = OrderLine(
        order=order, type=OrderLineType.OTHER, text="Special service 100$/h", quantity=1, base_unit_price_value=100
    )
    other_line_with_quantity.save()
    order.lines.add(other_line_with_quantity)

    assert other_line_with_quantity.max_refundable_quantity == 1
    assert other_line_with_quantity.max_refundable_amount.value == 100

    order.cache_prices()
    order.create_payment(order.taxful_total_price)
    assert order.is_paid()
    assert order.taxful_total_price_value == 120  # 100 + 4 * 20

    def get_refund_view_content():
        request = apply_request_middleware(rf.get("/"), user=admin_user)
        view = OrderCreateRefundView.as_view()
        response = view(request, pk=order.pk)
        return BeautifulSoup(response.render().content)

    refund_soup = get_refund_view_content()
    refund_options = refund_soup.find(id="id_form-0-line_number").findAll("option")
    assert len(refund_options) == 4  # 1 empty line, 1 for arbitrary and 2 for lines
    assert len([option for option in refund_options if "Special service 100$/h" in force_text(option)]) == 1
