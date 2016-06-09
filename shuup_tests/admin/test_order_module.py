# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.admin.modules.orders.dashboard import OrderValueChartDashboardBlock
from shuup.admin.modules.orders.views import (
    NewLogEntryView, OrderSetStatusView
)
from shuup.core.models import (
    Order, OrderLogEntry, OrderStatus, OrderStatusRole, ShippingStatus
)
from shuup.testing.factories import (
    create_random_order, create_random_person, get_default_product
)
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_order_set_status_completed_works(admin_user, rf):
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
def test_order_set_status_canceled_works(admin_user, rf):
    order = create_random_order(customer=create_random_person(), products=(get_default_product(),))
    assert order.shipping_status == ShippingStatus.NOT_SHIPPED
    assert order.status.role == OrderStatusRole.INITIAL
    canceled_status = OrderStatus.objects.get_default_canceled()
    view = OrderSetStatusView.as_view()
    request = apply_request_middleware(rf.post("/", {"status": canceled_status.pk}), user=admin_user)
    response = view(request, pk=order.pk)
    assert response.status_code < 400
    order = Order.objects.get(pk=order.pk)
    assert order.status_id == canceled_status.id
    assert order.log_entries.filter(identifier="status_change").exists()


@pytest.mark.django_db
def test_add_order_log_entry(admin_user, rf):
    order = create_random_order(customer=create_random_person(), products=(get_default_product(),))
    assert not OrderLogEntry.objects.filter(target=order).exists()
    view = NewLogEntryView.as_view()
    test_message = "test_order"
    request = apply_request_middleware(rf.post("/", {"message": test_message}), user=admin_user)
    response = view(request, pk=order.pk)
    assert response.status_code < 400
    assert OrderLogEntry.objects.filter(target=order).exists()
    assert OrderLogEntry.objects.filter(target=order).first().message == test_message


@pytest.mark.django_db
def test_order_chart_works():
    order = create_random_order(customer=create_random_person(), products=(get_default_product(),))
    chart = OrderValueChartDashboardBlock("test", order.currency).get_chart()
    assert len(chart.series[0]) > 0
