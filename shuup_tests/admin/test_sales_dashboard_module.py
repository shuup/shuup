# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from datetime import date

import pytest
from bs4 import BeautifulSoup

from shuup.admin.modules.sales_dashboard.dashboard import (
    get_recent_orders_block, get_shop_overview_block,
    OrderValueChartDashboardBlock
)
from shuup.core.models import OrderStatus
from shuup.testing.factories import (
    create_product, create_random_order, create_random_person,
    DEFAULT_CURRENCY, get_default_product, get_default_shop
)

NUM_ORDERS_COLUMN_INDEX = 2

def get_order_for_date(dt, product):
    order = create_random_order(customer=create_random_person(), products=[product])
    order.order_date = dt
    order.status = OrderStatus.objects.get_default_complete()
    order.save()
    return order

@pytest.mark.django_db
def test_order_chart_works():
    order = create_random_order(customer=create_random_person(), products=(get_default_product(),))
    chart = OrderValueChartDashboardBlock("test", order.currency).get_chart()
    assert len(chart.datasets[0]) > 0


@pytest.mark.django_db
def test_shop_overview_block(rf):
    today = date.today()
    product = get_default_product()
    sp = product.get_shop_instance(get_default_shop())
    sp.default_price_value = "10"
    sp.save()
    get_order_for_date(today, product)
    get_order_for_date(date(today.year, 1, 1), product)
    get_order_for_date(date(today.year, today.month, 1), product)

    block = get_shop_overview_block(rf.get("/"), DEFAULT_CURRENCY)
    soup = BeautifulSoup(block.content)
    _, today, mtd, ytd, totals = soup.find_all("tr")
    assert today.find_all("td")[NUM_ORDERS_COLUMN_INDEX].string == "1"
    assert mtd.find_all("td")[NUM_ORDERS_COLUMN_INDEX].string == "2"
    assert ytd.find_all("td")[NUM_ORDERS_COLUMN_INDEX].string == "3"
    assert totals.find_all("td")[NUM_ORDERS_COLUMN_INDEX].string == "3"


@pytest.mark.django_db
def test_recent_orders_block(rf):
    order = create_random_order(customer=create_random_person(), products=[get_default_product()])
    block = get_recent_orders_block(rf.get("/"), DEFAULT_CURRENCY)
    assert order.customer.name in block.content
