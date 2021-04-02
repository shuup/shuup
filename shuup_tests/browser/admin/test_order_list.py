# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os
import pytest

from shuup.core.models import Order, OrderStatus
from shuup.testing.browser_utils import (
    click_element,
    initialize_admin_browser_test,
    wait_until_appeared,
    wait_until_condition,
)
from shuup.testing.factories import create_empty_order, get_default_shop
from shuup.utils.django_compat import reverse

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.django_db
@pytest.mark.skipif(os.environ.get("SHUUP_TESTS_CI", "0") == "1", reason="Disable when run in CI.")
def test_orders_list_view(browser, admin_user, live_server, settings):
    shop = get_default_shop()
    for i in range(0, 9):
        order = create_empty_order(shop=shop)
        order.save()

    # Set last one canceled
    Order.objects.last().set_canceled()

    initialize_admin_browser_test(browser, live_server, settings)
    _visit_orders_list_view(browser, live_server)
    _test_status_filter(browser)  # Will set three orders from end canceled


def _visit_orders_list_view(browser, live_server):
    url = reverse("shuup_admin:order.list")
    browser.visit("%s%s" % (live_server, url))
    wait_until_condition(browser, condition=lambda x: x.is_text_present("Orders"))
    wait_until_appeared(browser, ".picotable-item-info")


def _test_status_filter(browser):
    # Check initial row count where the cancelled order should be excluded
    _check_row_count(browser, Order.objects.count())

    # Take three last valid orders and set those cancelled
    orders = Order.objects.valid()[:3]
    for order in orders:
        order.set_canceled()

    # Filter with cancelled
    cancelled_status = OrderStatus.objects.get_default_canceled()
    _change_status_filter(browser, "%s" % cancelled_status.pk)

    # Check cancelled row count
    _check_row_count(browser, (3 + 1))

    # Filter with initial
    initial_status = OrderStatus.objects.get_default_initial()
    _change_status_filter(browser, "%s" % initial_status.pk)

    # Take new count
    _check_row_count(browser, (Order.objects.count() - 3 - 1))

    # Change status filter to all
    _change_status_filter(browser, '"_all"')

    # Now all orders should be visible
    _check_row_count(browser, Order.objects.count())


def _check_row_count(browser, expected_row_count):
    wait_until_condition(browser, lambda x: len(x.find_by_css("#picotable tbody tr")) == expected_row_count)
    # technically this is handled above, but do the assertion anyways ;)
    assert len(browser.find_by_css("#picotable tbody tr")) == expected_row_count


def _change_status_filter(browser, to_value):
    click_element(browser, "#dropdownFilter")
    click_element(browser, "#picotable div.choice-filter")
    target = "#picotable div.choice-filter option[value='%s']" % to_value
    click_element(browser, target)  # TODO: Travis is not able to do this click. There is nothing wrong with the filter.
    browser.find_by_css("h1").first.click()
