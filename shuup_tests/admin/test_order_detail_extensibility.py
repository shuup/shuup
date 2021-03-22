# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import decimal
import pytest
from bs4 import BeautifulSoup

from shuup.admin.modules.orders.utils import OrderInformation
from shuup.admin.modules.orders.views.detail import OrderDetailView
from shuup.apps.provides import override_provides
from shuup.testing.factories import (
    add_product_to_order,
    create_empty_order,
    create_product,
    get_default_shop,
    get_default_supplier,
)
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import reverse


@pytest.mark.django_db
@pytest.mark.parametrize("has_price", (True, False))
def test_order_detail_has_default_toolbar_action_items(rf, admin_user, has_price):
    shop = get_default_shop()
    supplier = get_default_supplier()
    order = _get_order(shop, supplier, has_price)
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    view_func = OrderDetailView.as_view()
    create_payment_url = reverse("shuup_admin:order.create-payment", kwargs={"pk": order.pk})
    set_paid_url = reverse("shuup_admin:order.set-paid", kwargs={"pk": order.pk})
    with override_provides(
        "admin_order_toolbar_action_item",
        [
            "shuup.admin.modules.orders.toolbar:CreatePaymentAction",
            "shuup.admin.modules.orders.toolbar:SetPaidAction",
        ],
    ):
        if has_price:
            assert _check_if_link_exists(view_func, request, order, create_payment_url)
        else:
            assert _check_if_button_exists(view_func, request, order, set_paid_url)

    with override_provides("admin_order_toolbar_action_item", []):
        assert not _check_if_link_exists(view_func, request, order, create_payment_url)


def _check_if_button_exists(view_func, request, order, url):
    response = view_func(request, pk=order.pk)
    soup = BeautifulSoup(response.render().content)
    for dropdown_btn in soup.find_all("button", {"class": "dropdown-item"}):
        if dropdown_btn.get("formaction", "") == url:
            return True
    return False


def _check_if_link_exists(view_func, request, order, url):
    response = view_func(request, pk=order.pk)
    soup = BeautifulSoup(response.render().content)
    for dropdown_link in soup.find_all("a", {"class": "dropdown-item"}):
        if dropdown_link.get("href", "") == url:
            return True
    return False


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


class PaymentMethodName(OrderInformation):
    title = "Extra information row"

    @property
    def information(self):
        return "This is row data"


@pytest.mark.django_db
def test_order_detail_info_row_extend(rf, admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    order = _get_order(shop, supplier, True)
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    view_func = OrderDetailView.as_view()

    # Test that we can insert extra information rows into Order detail page
    with override_provides(
        "admin_order_information",
        [
            "shuup_tests.admin.test_order_detail_extensibility:PaymentMethodName",
        ],
    ):
        response = view_func(request, pk=order.pk)
        soup = BeautifulSoup(response.render().content)
        assert soup.find_all(text="This is row data")
