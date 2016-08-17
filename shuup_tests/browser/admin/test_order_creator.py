# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import decimal
import os
import time

import pytest
from django.core.urlresolvers import reverse

from shuup.core.models import Order, OrderStatus
from shuup.testing.browser_utils import (
    move_to_element, wait_until_appeared, wait_until_disappeared
)
from shuup.testing.factories import (
    create_empty_order, create_product, create_random_person,
    get_default_payment_method, get_default_shipping_method, get_default_shop,
    get_default_supplier, get_initial_order_status
)
from shuup.testing.utils import initialize_admin_browser_test

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.browser
@pytest.mark.djangodb
def test_order_creator_view(browser, admin_user, live_server):
    shop = get_default_shop()
    pm = get_default_payment_method()
    sm = get_default_shipping_method()
    get_initial_order_status()
    supplier = get_default_supplier()
    person = create_random_person()
    product0 = create_product("test-sku0", shop=shop, default_price=10, supplier=supplier)
    product1 = create_product("test-sku1", shop=shop, default_price=10, supplier=supplier)

    initialize_admin_browser_test(browser, live_server)
    _visit_order_creator_view(browser, live_server)
    _test_customer_data(browser, person)
    _test_add_lines(browser)
    _test_quick_add_lines(browser)
    _test_methods(browser)
    _test_confirm(browser)


def _visit_order_creator_view(browser, live_server):
    browser.execute_script("window.localStorage.setItem('resetSavedOrder', 'true')")
    url = reverse("shuup_admin:order.new")
    browser.visit("%s%s" % (live_server, url))
    assert browser.is_element_present_by_css("h1.main-header")


def _test_customer_data(browser, person):
    # check defaults
    assert browser.find_by_css("input[name='save-address']").first.checked == True
    assert browser.find_by_css("input[name='ship-to-billing-address']").first.checked == False
    assert browser.find_by_css("input[name='order-for-company']").first.checked == False
    assert not browser.find_by_css("input[name='billing-tax_number']").first['required']
    browser.check("ship-to-billing-address")
    browser.check("order-for-company")
    assert len(browser.find_by_css("input[name='shipping-name']")) == 0, "shipping address column is hidden"
    assert browser.find_by_css("input[name='billing-tax_number']").first['required'], "tax number is required"

    browser.uncheck("order-for-company")
    browser.find_by_id("select-existing-customer").click()
    browser.windows.current = browser.windows[1]
    wait_until_appeared(browser, "a")
    # click second row - first row is admin
    browser.find_by_css("tbody tr")[1].find_by_css("a").click()
    browser.windows.current = browser.windows[0]
    # check fields were set
    assert browser.find_by_name("billing-name").value == person.name
    assert browser.find_by_name("billing-street").value == person.default_billing_address.street
    assert browser.find_by_name("billing-city").value == person.default_billing_address.city
    assert browser.find_by_name("billing-country").value == person.default_billing_address.country


def _test_add_lines(browser):
    line_items_before = browser.find_by_id("lines").find_by_css('.list-group-item')
    move_to_element(browser, "#lines")
    browser.find_by_id("add-line").click()
    line_items_after = browser.find_by_id("lines").find_by_css('.list-group-item')
    assert len(line_items_after) == len(line_items_before) + 1, "new line added"
    last_line_item = line_items_after[len(line_items_after) - 1]

    # select product
    last_line_item.find_by_tag('a').click()
    browser.windows.current = browser.windows[1]
    wait_until_appeared(browser, "a")
    browser.find_by_css("tbody a").first.click()
    browser.windows.current = browser.windows[0]
    wait_until_appeared(browser, ".text-info")
    assert last_line_item.find_by_css('input[name="quantity"]').first.value == "1", "1 piece added"
    assert last_line_item.find_by_css('input[name="total"]').first.value == "10", "line item total is 10"
    last_line_item.find_by_css(".delete button").click()
    line_items_after = browser.find_by_id("lines").find_by_css('.list-group-item')
    assert len(line_items_before) == len(line_items_after), "line item removed"


def _test_quick_add_lines(browser):
    assert browser.find_by_css("input[name='auto-add']").first.checked == True
    # add line automatically just by searching and finding direct match
    #browser.execute_script("window.scrollTo(0, $('#quick-add').offset().top)")
    move_to_element(browser, "#quick-add")
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
    wait_until_disappeared(browser, '.select2-container--open')
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


def _test_methods(browser):
    # check defaults
    assert browser.find_by_name("shipping").value == "0"
    assert browser.find_by_name("payment").value == "0"
    browser.select("shipping", 1)
    browser.select("payment", 1)


def _test_confirm(browser):
    total = sum([decimal.Decimal(total_el.value) for total_el in browser.find_by_css("input[name='total']")])
    assert str(total) in browser.find_by_css(".order-footer h2").text, "order total is correct"
    browser.find_by_css(".order-footer button").click()
    wait_until_appeared(browser, "table")
    assert len(browser.find_by_css("table tbody tr")) == 5, "2 line items, 2 methods, 1 total line shown in confirmation table"
    # click confirm
    browser.find_by_css(".btn-success").click()
    wait_until_appeared(browser, "#details-status-section")
    assert Order.objects.count() == 1, "order created"
