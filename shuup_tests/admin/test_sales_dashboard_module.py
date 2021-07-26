# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from bs4 import BeautifulSoup
from datetime import date
from django.test import override_settings

from shuup.admin.modules.sales_dashboard.dashboard import (
    OrderValueChartDashboardBlock,
    get_recent_orders_block,
    get_shop_overview_block,
)
from shuup.core.models import ShopStatus
from shuup.testing.factories import (
    DEFAULT_CURRENCY,
    create_random_order,
    create_random_person,
    get_completed_order_status,
    get_default_product,
    get_default_shop,
    get_shop,
)
from shuup.testing.utils import apply_request_middleware
from shuup.utils.dates import to_aware

NUM_ORDERS_COLUMN_INDEX = 2
NUM_CUSTOMERS_COLUMN_INDEX = 3


def get_order_for_date(dt, product):
    order = create_random_order(customer=create_random_person(), products=[product])
    order.order_date = to_aware(dt)
    order.change_status(get_completed_order_status(), save=False)
    order.save()
    return order


@pytest.mark.django_db
def test_order_chart_works(rf, admin_user):
    get_default_shop()
    order = create_random_order(customer=create_random_person(), products=(get_default_product(),))
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    chart = OrderValueChartDashboardBlock("test", request=request).get_chart()
    assert len(chart.datasets[0]) > 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    "data",
    [
        # date, today, mtd, ytd
        (date(1976, 3, 6), 2, 3, 4),
        (date(2005, 9, 15), 2, 3, 4),
        (date(2012, 7, 1), 3, 3, 4),
        (date(2016, 1, 1), 4, 4, 4),
        (date(2016, 12, 31), 2, 3, 4),
        (date(2020, 2, 29), 2, 3, 4),
    ],
)
def test_shop_overview_block(rf, data, admin_user):
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        shop1 = get_default_shop()
        shop2 = get_shop(identifier="shop2", status=ShopStatus.ENABLED, name="Shop2")

        (today, expected_today, expected_mtd, expected_ytd) = data
        product = get_default_product()
        sp = product.get_shop_instance(shop1)
        sp.default_price_value = "10"
        sp.save()
        get_order_for_date(today, product)
        o = get_order_for_date(today, product)
        o.customer = None
        o.save()
        get_order_for_date(date(today.year - 1, 12, 31), product)
        get_order_for_date(date(today.year, 1, 1), product)
        get_order_for_date(date(today.year, today.month, 1), product)

        for shop in [shop1, shop2]:
            request = apply_request_middleware(rf.get("/"), user=admin_user, shop=shop)
            block = get_shop_overview_block(request, currency=DEFAULT_CURRENCY, for_date=today)
            soup = BeautifulSoup(block.content)
            _, today_sales, mtd, ytd, totals = soup.find_all("tr")

            if shop == shop1:
                assert today_sales.find_all("td")[NUM_ORDERS_COLUMN_INDEX].string == str(expected_today)
                assert today_sales.find_all("td")[NUM_CUSTOMERS_COLUMN_INDEX].string == str(expected_today)
                assert mtd.find_all("td")[NUM_ORDERS_COLUMN_INDEX].string == str(expected_mtd)
                assert mtd.find_all("td")[NUM_CUSTOMERS_COLUMN_INDEX].string == str(expected_mtd)
                assert ytd.find_all("td")[NUM_ORDERS_COLUMN_INDEX].string == str(expected_ytd)
                assert ytd.find_all("td")[NUM_CUSTOMERS_COLUMN_INDEX].string == str(expected_ytd)
                assert totals.find_all("td")[NUM_ORDERS_COLUMN_INDEX].string == "5"
                assert totals.find_all("td")[NUM_CUSTOMERS_COLUMN_INDEX].string == "5"
            else:
                assert today_sales.find_all("td")[NUM_ORDERS_COLUMN_INDEX].string == "0"
                assert today_sales.find_all("td")[NUM_CUSTOMERS_COLUMN_INDEX].string == "0"
                assert mtd.find_all("td")[NUM_ORDERS_COLUMN_INDEX].string == "0"
                assert mtd.find_all("td")[NUM_CUSTOMERS_COLUMN_INDEX].string == "0"
                assert ytd.find_all("td")[NUM_ORDERS_COLUMN_INDEX].string == "0"
                assert ytd.find_all("td")[NUM_CUSTOMERS_COLUMN_INDEX].string == "0"
                assert totals.find_all("td")[NUM_ORDERS_COLUMN_INDEX].string == "0"
                assert totals.find_all("td")[NUM_CUSTOMERS_COLUMN_INDEX].string == "0"


@pytest.mark.django_db
def test_recent_orders_block(rf, admin_user):
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=True):
        shop1 = get_default_shop()
        shop2 = get_shop(identifier="shop2", status=ShopStatus.ENABLED, name="Shop2")
        customer = create_random_person()
        # prevent weird names with random chars
        customer.name = "Jon Doe"
        customer.save()
        order = create_random_order(customer=customer, products=[get_default_product()])

        for shop in [shop1, shop2]:
            request = apply_request_middleware(rf.get("/"), user=admin_user, shop=shop)
            block = get_recent_orders_block(request)

            if shop == shop1:
                assert order.customer.name in block.content
            else:
                assert order.customer.name not in block.content
