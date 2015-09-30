# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from shoop.admin.modules.orders.dashboard import OrderValueChartDashboardBlock
from shoop.admin.modules.orders.views.detail import OrderSetStatusView
from shoop.core.models.orders import OrderStatusRole, OrderStatus, Order
from shoop.testing.factories import create_random_order, get_default_product, create_random_person
from shoop_tests.utils import apply_request_middleware


@pytest.mark.django_db
def test_order_set_status_works(admin_user, rf):
    order = create_random_order(customer=create_random_person(), products=(get_default_product(),))
    order.create_shipment_of_all_products()  # Need to be shipped to set complete
    assert order.status.role == OrderStatusRole.INITIAL
    complete_status = OrderStatus.objects.get_default_complete()
    view = OrderSetStatusView.as_view()
    request = apply_request_middleware(rf.post("/", {"status": complete_status.pk}), user=admin_user)
    response = view(request, pk=order.pk)
    assert response.status_code < 400
    order = Order.objects.get(pk=order.pk)
    assert order.status_id == complete_status.id
    assert order.log_entries.filter(identifier="status_change").exists()


@pytest.mark.django_db
def test_order_chart_works():
    order = create_random_order(customer=create_random_person(), products=(get_default_product(),))
    chart = OrderValueChartDashboardBlock("test", order.currency).get_chart()
    assert len(chart.series[0]) > 0
