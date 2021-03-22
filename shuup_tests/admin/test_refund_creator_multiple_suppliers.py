# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
import six
from bs4 import BeautifulSoup
from collections import defaultdict
from decimal import Decimal
from django.test import override_settings

from shuup.admin.modules.orders.views.refund import OrderCreateRefundView
from shuup.admin.supplier_provider import get_supplier
from shuup.core.excs import NoRefundToCreateException
from shuup.core.models import OrderLineType, ShippingMode, Supplier
from shuup.testing.factories import add_product_to_order, create_empty_order, create_product, get_default_shop
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_refunds_with_multiple_suppliers(rf, admin_user):
    shop = get_default_shop()
    supplier1 = Supplier.objects.create(identifier="1", name="supplier1")
    supplier1.shops.add(shop)

    supplier2 = Supplier.objects.create(identifier="2")
    supplier2.shops.add(shop)

    supplier3 = Supplier.objects.create(identifier="3", name="s")
    supplier3.shops.add(shop)

    product1 = create_product("sku1", shop=shop, default_price=10)
    shop_product1 = product1.get_shop_instance(shop=shop)
    shop_product1.suppliers.set([supplier1, supplier2, supplier3])

    product2 = create_product("sku2", shop=shop, default_price=10)
    shop_product2 = product1.get_shop_instance(shop=shop)
    shop_product2.suppliers.set([supplier1, supplier2])

    product3 = create_product("sku3", shop=shop, default_price=10, shipping_mode=ShippingMode.NOT_SHIPPED)
    shop_product3 = product1.get_shop_instance(shop=shop)
    shop_product3.suppliers.set([supplier3])

    product_quantities = {
        supplier1: {product1: 5, product2: 6},
        supplier2: {product1: 3, product2: 13},
        supplier3: {product1: 1, product3: 50},
    }

    def get_quantity(supplier, product):
        return product_quantities[supplier.pk][product.pk]

    order = create_empty_order(shop=shop)
    order.full_clean()
    order.save()

    for supplier, product_data in six.iteritems(product_quantities):
        for product, quantity in six.iteritems(product_data):
            add_product_to_order(order, supplier, product, quantity, 5)

    order.cache_prices()
    order.create_payment(order.taxful_total_price)
    assert order.is_paid()

    # All supplier should be able to refund the order
    assert order.can_create_refund()
    assert order.can_create_refund(supplier1)
    assert order.can_create_refund(supplier2)
    assert order.can_create_refund(supplier3)

    assert not order.has_refunds()
    assert len(order.lines.all()) == 6

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

    supplier_provider = "shuup.testing.supplier_provider.RequestSupplierProvider"
    with override_settings(SHUUP_ADMIN_SUPPLIER_PROVIDER_SPEC=supplier_provider):
        # Test refund view content as superuser
        request = apply_request_middleware(rf.get("/", data=data), user=admin_user)
        view = OrderCreateRefundView.as_view()
        response = view(request, pk=order.pk)
        assert response.status_code == 200
        if hasattr(response, "render"):
            response.render()

        soup = BeautifulSoup(response.content)
        _assert_order_table_row_count(soup, 6)
        _assert_order_mobile_list_row_count(soup, 6)
        assert _get_create_full_refund_button(soup) is not None

        # Test refund view content as supplier 1
        request = apply_request_middleware(rf.get("/", data=data), user=admin_user)
        request.supplier = supplier1
        assert get_supplier(request) == supplier1

        view = OrderCreateRefundView.as_view()
        response = view(request, pk=order.pk)
        assert response.status_code == 200
        if hasattr(response, "render"):
            response.render()

        soup = BeautifulSoup(response.content)
        _assert_order_table_row_count(soup, 2)
        _assert_order_mobile_list_row_count(soup, 2)
        assert _get_create_full_refund_button(soup) is None

        # Test refund view content as supplier 2 user
        request = apply_request_middleware(rf.get("/", data=data), user=admin_user)
        request.supplier = supplier2
        assert get_supplier(request) == supplier2

        view = OrderCreateRefundView.as_view()
        response = view(request, pk=order.pk)
        assert response.status_code == 200
        if hasattr(response, "render"):
            response.render()

        soup = BeautifulSoup(response.content)
        _assert_order_table_row_count(soup, 2)
        _assert_order_mobile_list_row_count(soup, 2)
        assert _get_create_full_refund_button(soup) is None


def _assert_order_table_row_count(soup, expected_count):
    assert len(soup.select("table tbody tr")) == expected_count


def _assert_order_mobile_list_row_count(soup, expected_count):
    assert len(soup.findAll("li", {"class": "list-group-item"})) == expected_count


def _get_create_full_refund_button(soup):
    return soup.find("div", {"class": "btn-toolbar"}).find("a", {"class": "btn-info"})
