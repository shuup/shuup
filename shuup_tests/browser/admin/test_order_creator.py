# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import os
import pytest
import time

from django.core.urlresolvers import reverse

from shuup.core.models import Order, OrderStatus
from shuup.testing.factories import create_empty_order, get_default_shop, create_product
from shuup.testing.utils import initialize_admin_browser_test
from shuup.testing.browser_utils import wait_until_disappeared


pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.browser
@pytest.mark.djangodb
def test_order_creator_view(browser, admin_user, live_server):
    shop = get_default_shop()
    product0 = create_product("test-sku0", shop=shop)
    product1 = create_product("test-sku1", shop=shop)

    initialize_admin_browser_test(browser, live_server)
    _visit_order_creator_view(browser, live_server)
    _test_quick_add_lines(browser)


def _visit_order_creator_view(browser, live_server):
    browser.execute_script("window.localStorage.setItem('resetSavedOrder', 'true')")
    url = reverse("shuup_admin:order.new")
    browser.visit("%s%s" % (live_server, url))
    assert browser.is_element_present_by_css("h1.main-header")


def _test_quick_add_lines(browser):
    assert browser.find_by_css("input[name='auto-add']").first.checked == True
    # add line automatically just by searching and finding direct match
    browser.execute_script("window.scrollTo(0, document.getElementById('quick-add').getBoundingClientRect().top - 200)")
    browser.find_by_id("quick-add").find_by_css('.select2').click()

    assert len(browser.find_by_id("quick-add").find_by_css('.select2-container--open')) == 1, "select is open"
    browser.find_by_css("input.select2-search__field").first.value = "test-sku1"
    wait_until_disappeared(browser, "select2-results__message")
    line_items = browser.find_by_id("lines").find_by_css('.list-group-item')
    assert len(line_items) == 1, "one line item added"
    assert len(browser.find_by_id("quick-add").find_by_css('.select2-container--open')) == 1, "select is open after add"
    assert line_items.first.find_by_css('input[name="quantity"]').first.value == '1', "one piece added"

    browser.find_by_css("input.select2-search__field").first.value = "test-sku1"
    wait_until_disappeared(browser, "select2-results__message")
    line_items = browser.find_by_id("lines").find_by_css('.list-group-item')
    assert len(line_items) == 1, "only one line item exists"
    assert line_items.first.find_by_css('input[name="quantity"]').first.value == '2', "two pieces added"

    # add line automatically by searching and clicking on match
    browser.find_by_css("input.select2-search__field").first.value = "test-sku"
    wait_until_disappeared(browser, "select2-results__message")
    browser.execute_script('$($(".select2-results__option")[0]).trigger({type: "mouseup"})')
    assert line_items.first.find_by_css('input[name="quantity"]').first.value == '3', "three pieces added"

    # add line manually
    browser.uncheck("auto-add")
    browser.find_by_id("quick-add").find_by_css('.select2').click()
    browser.find_by_css("input.select2-search__field").first.value = "test-sku0"
    wait_until_disappeared(browser, "select2-results__message")
    browser.execute_script('$($(".select2-results__option")[0]).trigger({type: "mouseup"})')
    browser.find_by_id("add-product").first.click()
    line_items = browser.find_by_id("lines").find_by_css('.list-group-item')
    assert len(line_items) == 2, "two line items exist"
