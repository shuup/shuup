# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import os
import time

from django.core.urlresolvers import reverse

import pytest
from shuup.core.models import Order, OrderStatus
from shuup.testing.browser_utils import wait_until_appeared
from shuup.testing.factories import create_empty_order, get_default_shop
from shuup.testing.utils import initialize_admin_browser_test

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.browser
@pytest.mark.djangodb
def test_orders_list_view(browser, admin_user, live_server):
    shop = get_default_shop()
    for i in range(0, 10):
        order = create_empty_order(shop=shop)
        order.save()

    # Set last one canceled
    Order.objects.last().set_canceled()

    initialize_admin_browser_test(browser, live_server)
    _visit_orders_list_view(browser, live_server)
    _test_status_filter(browser)  # Will set three orders from end canceled


def _visit_orders_list_view(browser, live_server):
    url = reverse("shuup_admin:order.list")
    browser.visit("%s%s" % (live_server, url))
    assert browser.is_text_present("Orders")
    wait_until_appeared(browser, css_class=".picotable-item-info")


def _test_status_filter(browser):
    # Get initial row count where the cancelled order should be excluded
    row_count = _get_row_count_from_picotable(browser)
    assert row_count == Order.objects.count() - 1  # Since one is cancelled

    # Take three last valid orders and set those cancelled
    orders = Order.objects.valid()[:3]
    for order in orders:
        order.set_canceled()

    # Filter with cancelled
    cancelled_status = OrderStatus.objects.get_default_canceled()
    _change_status_filter(browser, "%s" % cancelled_status.pk)

    # Take new count
    cancelled_count = _get_row_count_from_picotable(browser)
    assert cancelled_count == (3 + 1)

    # Filter with initial
    initial_status = OrderStatus.objects.get_default_initial()
    _change_status_filter(browser, "%s" % initial_status.pk)

    # Take new count
    received_count = _get_row_count_from_picotable(browser)
    assert received_count == (Order.objects.count() - 3 - 1)

    # Change status filter to all
    _change_status_filter(browser, '"_all"')

    # Now all orders should be visible
    received_count = _get_row_count_from_picotable(browser)
    assert received_count == Order.objects.count()


def _get_row_count_from_picotable(browser):
    picotable = browser.find_by_id("picotable")
    tbody = picotable.find_by_tag("tbody").first
    return len(tbody.find_by_tag("tr"))


def _change_status_filter(browser, to_value):
    picotable = browser.find_by_id("picotable")
    choice_filter = picotable.find_by_css("div.choice-filter").first
    choice_filter.click()
    choice_filter.find_by_xpath("//option[@value='%s']" % to_value).first.click()
    time.sleep(0.5)  # Wait mithril for a half sec
