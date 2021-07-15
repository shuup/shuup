# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.contrib.auth import get_user_model

from shuup.core.models import OrderStatus, OrderStatusManager, OrderStatusRole
from shuup.front.apps.personal_order_history.dashboard_items import OrderHistoryItem
from shuup.front.apps.personal_order_history.views import OrderListView
from shuup.testing.factories import (
    create_product,
    create_random_address,
    create_random_order,
    create_random_person,
    create_random_user,
    get_default_shop,
    get_default_supplier,
)
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import reverse
from shuup_tests.utils import SmartClient

User = get_user_model()


@pytest.mark.django_db
def test_customer_order_history(rf):
    OrderStatusManager().ensure_default_statuses()

    # make processing status invisible for customer, will check it later.
    processing_status = OrderStatus.objects.filter(role=OrderStatusRole.PROCESSING).first()
    processing_status.visible_for_customer = False
    processing_status.save()

    # create new customer
    user = create_random_user("en")
    user_password = "1234"
    user.set_password(user_password)
    user.save()
    customer = create_random_person("en")
    customer.user = user
    customer.default_billing_address = create_random_address()
    customer.default_shipping_address = create_random_address()
    customer.save()

    # create new order and add 2 order status changes
    shop = get_default_shop()
    product = create_product("p", get_default_shop(), get_default_supplier())
    order = create_random_order(
        customer=customer,
        shop=shop,
        products=(product,),
        create_payment_for_order_total=False,
    )
    order.change_status(OrderStatus.objects.get_default_processing())
    order.change_status(OrderStatus.objects.get_default_complete())

    # check the context generated in the dashboard view
    url = reverse("shuup:dashboard")
    request = apply_request_middleware(rf.get(url), user=user)
    view = OrderHistoryItem(request)
    context = view.get_context()
    assert len(context["order_status_history"]) == 2

    # check the context generated in the order history view
    url = reverse("shuup:personal-orders")
    request = apply_request_middleware(rf.get(url), user=user)
    view = OrderListView()
    view.request = request
    view.object_list = view.get_queryset()
    view.get_queryset()
    context = view.get_context_data()
    assert len(context["order_status_history"]) == 2

    # check the resulting render in the order history page
    url = reverse("shuup:personal-orders")
    client = SmartClient()
    client.login(username=user.username, password=user_password)
    response, soup = client.response_and_soup(url)
    tbody = soup.find_all("tbody")
    assert tbody
    tr = tbody[0].find_all("tr")
    assert len(tr) == 2

    # check the resulting render in the dashboard page
    url = reverse("shuup:dashboard")
    response, soup = client.response_and_soup(url)
    d = soup.find_all(id="dashboard-content")
    assert d
    order_history_div = d[0].find_all(id="order_history")
    assert order_history_div
    tbody = order_history_div[0].find_all("tbody")
    assert tbody
    tr = tbody[0].find_all("tr")
    assert len(tr) == 2
