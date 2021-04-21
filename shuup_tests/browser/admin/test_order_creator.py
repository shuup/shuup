# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import decimal
import os
import pytest
from splinter.exceptions import ElementDoesNotExist

from shuup.admin.signals import object_created
from shuup.core.models import Order
from shuup.testing.browser_utils import (
    click_element,
    initialize_admin_browser_test,
    move_to_element,
    wait_until_appeared,
    wait_until_condition,
)
from shuup.testing.factories import (
    create_product,
    create_random_person,
    get_default_payment_method,
    get_default_shipping_method,
    get_default_shop,
    get_default_supplier,
    get_initial_order_status,
)
from shuup.utils.django_compat import reverse

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")
OBJECT_CREATED_LOG_IDENTIFIER = "object_created_signal_handled"


@pytest.mark.django_db
@pytest.mark.skipif(os.environ.get("SHUUP_TESTS_CI", "0") == "1", reason="Disable when run in CI.")
def test_order_creator_view_1(browser, admin_user, live_server, settings):
    shop = get_default_shop()
    get_default_payment_method()
    get_default_shipping_method()
    get_initial_order_status()
    supplier = get_default_supplier()
    person = create_random_person()
    person.shops.add(shop)

    create_product("test-sku0", shop=shop, default_price=10, supplier=supplier)
    create_product("test-sku1", shop=shop, default_price=10, supplier=supplier)
    object_created.connect(_add_custom_order_created_message, sender=Order, dispatch_uid="object_created_signal_test")

    initialize_admin_browser_test(browser, live_server, settings)
    _visit_order_creator_view(browser, live_server)
    _test_language_change(browser)
    _test_customer_data(browser, person)
    _test_regions(browser, person)
    _test_quick_add_lines(browser)


@pytest.mark.django_db
@pytest.mark.skipif(os.environ.get("SHUUP_TESTS_CI", "0") == "1", reason="Disable when run in CI.")
def test_order_creator_view_2(browser, admin_user, live_server, settings):
    shop = get_default_shop()
    pm = get_default_payment_method()
    sm = get_default_shipping_method()
    get_initial_order_status()
    supplier = get_default_supplier()
    person = create_random_person()
    person.registration_shop = shop
    person.save()
    person.shops.add(shop)

    create_product("test-sku0", shop=shop, default_price=10, supplier=supplier)
    create_product("test-sku1", shop=shop, default_price=10, supplier=supplier)
    object_created.connect(_add_custom_order_created_message, sender=Order, dispatch_uid="object_created_signal_test")

    initialize_admin_browser_test(browser, live_server, settings)
    original_size = browser.driver.get_window_size()
    browser.driver.set_window_size(1920, 1080)
    _visit_order_creator_view(browser, live_server)
    _test_customer_using_search(browser, person)
    _test_add_lines(browser)
    _test_methods(browser, sm, pm)
    _test_confirm(browser)
    assert Order.objects.first().log_entries.filter(identifier=OBJECT_CREATED_LOG_IDENTIFIER).count() == 1
    object_created.disconnect(sender=Order, dispatch_uid="object_created_signal_test")
    browser.driver.set_window_size(original_size["width"], original_size["height"])


def _add_custom_order_created_message(sender, object, **kwargs):
    assert sender == Order
    object.add_log_entry("Custom object created signal handled", identifier=OBJECT_CREATED_LOG_IDENTIFIER)


def _visit_order_creator_view(browser, live_server):
    browser.execute_script("window.localStorage.setItem('resetSavedOrder', 'true')")
    url = reverse("shuup_admin:order.new")
    browser.visit("%s%s" % (live_server, url))
    assert browser.is_element_present_by_css("h1.main-header")


def _test_language_change(browser):
    wait_until_condition(browser, lambda x: x.is_text_present("Customer Details"))

    # Make sure that the translations is handled correctly and change to Finnish
    browser.find_by_id("dropdownMenu").click()
    browser.find_by_xpath('//a[@data-value="fi"]').first.click()
    wait_until_condition(browser, condition=lambda x: x.is_text_present("Asiakkaan tiedot"))

    # And back in English
    browser.find_by_id("dropdownMenu").click()
    browser.find_by_xpath('//a[@data-value="en"]').first.click()
    wait_until_condition(browser, condition=lambda x: x.is_text_present("Customer Details"))


def _test_customer_using_search(browser, person):
    click_element(browser, "#customer-search .select2")
    wait_until_appeared(browser, "input.select2-search__field")
    browser.find_by_css("input.select2-search__field").first.value = person.first_name
    wait_until_appeared(browser, ".select2-results__option[aria-selected='false']")
    browser.execute_script('$($(".select2-results__option")[0]).trigger({type: "mouseup"})')
    wait_until_condition(browser, lambda x: len(x.find_by_css(".view-details-link")) == 1)


def _test_regions(browser, person):
    with pytest.raises(ElementDoesNotExist):
        browser.find_by_css("input[name='billing-region_code']").first
    assert browser.find_by_css("input[name='billing-region']").first
    move_to_element(browser, "input[name='billing-region']")  # To ensure all inputs required test is available

    browser.select("billing-country", "US")
    wait_until_appeared(browser, "select[name='billing-region_code']")
    with pytest.raises(ElementDoesNotExist):
        browser.find_by_css("input[name='billing-region']").first
    browser.select("billing-region_code", "CA")
    browser.select("billing-country", "CG")  # Congo does not have regions defined
    wait_until_appeared(browser, "input[name='billing-region']")
    browser.select("billing-country", person.default_billing_address.country)


def _test_quick_add_lines(browser):
    assert browser.find_by_css("input[name='auto-add']").first.checked == True
    # add line automatically just by searching and finding direct match
    click_element(browser, "#quick-add .select2")
    wait_until_condition(browser, lambda x: len(browser.find_by_css("#quick-add .select2-container--open")) == 1)
    browser.find_by_css("input.select2-search__field").first.value = "test-sku1"
    wait_until_condition(browser, lambda x: len(x.find_by_css("#lines .list-group-item")) == 1)
    line_items = browser.find_by_css("#lines .list-group-item")
    assert len(browser.find_by_css("#quick-add .select2-container--open")) == 1, "select is open after add"
    assert line_items.first.find_by_css('input[name="quantity"]').first.value == "1", "one piece added"

    browser.find_by_css("input.select2-search__field").first.value = "test-sku1"
    wait_until_condition(browser, lambda x: x.find_by_css('#lines input[name="quantity"]').first.value == "2")
    line_items = browser.find_by_id("lines").find_by_css(".list-group-item")
    assert len(line_items) == 1, "only one line item exists"
    assert line_items.first.find_by_css('input[name="quantity"]').first.value == "2", "two pieces added"

    # add line automatically by searching and clicking on match
    browser.find_by_css("input.select2-search__field").first.value = "test-sku"
    wait_until_appeared(browser, ".select2-results__option[aria-selected='false']")
    browser.execute_script('$($(".select2-results__option")[0]).trigger({type: "mouseup"})')
    wait_until_condition(browser, lambda x: x.find_by_css('#lines input[name="quantity"]').first.value == "3")
    assert line_items.first.find_by_css('input[name="quantity"]').first.value == "3", "three pieces added"

    # add line manually
    browser.uncheck("auto-add")
    click_element(browser, "#quick-add .select2")
    wait_until_appeared(browser, "input.select2-search__field")
    browser.find_by_css("input.select2-search__field").first.value = "test-sku0"
    wait_until_appeared(browser, ".select2-results__option[aria-selected='false']")
    browser.execute_script('$($(".select2-results__option")[0]).trigger({type: "mouseup"})')
    wait_until_condition(browser, lambda x: len(x.find_by_css("#lines .list-group-item")) == 2)
    line_items = browser.find_by_id("lines").find_by_css(".list-group-item")
    assert len(line_items) == 2, "two line items exist"

    click_element(browser, "#lines .list-group-item:last-child .delete button")
    wait_until_condition(browser, lambda x: len(x.find_by_css("#lines .list-group-item")) == 1)


def _test_customer_data(browser, person):
    browser.driver.execute_script("window.scrollTo(0, 200);")
    # check defaults
    assert browser.find_by_css("input[name='save-address']").first.checked == True
    assert browser.find_by_css("input[name='ship-to-billing-address']").first.checked == False
    assert browser.find_by_css("input[name='order-for-company']").first.checked == False
    assert not browser.find_by_css("input[name='billing-tax_number']").first["required"]
    browser.find_by_css("input[name=ship-to-billing-address]").check()
    assert browser.find_by_css("input[name=ship-to-billing-address]").first.checked
    browser.find_by_css("input[name='order-for-company']").check()
    assert browser.find_by_css("input[name='order-for-company']").first.checked
    wait_until_condition(browser, lambda x: x.find_by_css("input[name='billing-tax_number']").first["required"])
    assert len(browser.find_by_css("input[name='shipping-name']")) == 0, "shipping address column is hidden"

    browser.find_by_css("input[name='order-for-company']").uncheck()
    click_element(browser, "#select-existing-customer")
    browser.windows.current = browser.windows[1]
    wait_until_appeared(browser, "a")

    # click second row - first row is admin
    browser.find_by_css("tbody tr")[1].find_by_css("a").click()

    # Wait until there is only one window left
    # after that is safe to switch the current window
    # back and test the results of the customer pick.
    wait_until_condition(browser, lambda x: len(browser.windows) == 1, timeout=30)
    browser.windows.current = browser.windows[0]
    # check fields were set
    wait_until_condition(browser, lambda x: x.find_by_name("billing-name").value == person.name)
    assert browser.find_by_name("billing-name").value == person.name
    assert browser.find_by_name("billing-street").value == person.default_billing_address.street
    assert browser.find_by_name("billing-city").value == person.default_billing_address.city
    assert browser.find_by_name("billing-country").value == person.default_billing_address.country
    click_element(browser, "#clear-customer")
    wait_until_condition(browser, lambda x: "new customer" in x.find_by_css("#customer-description").text)


def _test_add_lines(browser):
    line_items_before = browser.find_by_id("lines").find_by_css(".list-group-item")
    click_element(browser, "#add-line")
    wait_until_condition(browser, lambda x: len(x.find_by_css("#lines .list-group-item")) == len(line_items_before) + 1)

    # Make sure that the lines is present before
    # selecting product for the order line.
    original_window_name = browser.windows.current.name
    wait_until_condition(browser, lambda x: x.is_element_present_by_css("#lines .list-group-item:last-child a"))

    click_element(browser, "#lines .list-group-item:last-child a")
    browser.windows.current = browser.windows[1]
    wait_until_appeared(browser, "a")
    browser.find_by_css("tbody tr")[1].find_by_css("a").click()

    # Wait until there is only one window left
    # after that is safe to switch the current window
    # back and test the results of the product pick.
    wait_until_condition(browser, lambda x: len(browser.windows) == 1, timeout=30)
    browser.windows.current = browser.windows[0]
    browser.windows.current.close_others()
    wait_until_condition(browser, lambda x: browser.windows.current.name == original_window_name, timeout=30)

    wait_until_condition(
        browser,
        lambda x: x.find_by_css('#lines .list-group-item:last-child input[name="total"]').first.value == "10",
        timeout=100,
    )
    last_line_item = browser.find_by_css("#lines .list-group-item:last-child")
    assert last_line_item.find_by_css('input[name="quantity"]').first.value == "1", "1 piece added"
    assert last_line_item.find_by_css('input[name="total"]').first.value == "10", "line item total is 10"


def _test_methods(browser, shipping_method, payment_method):
    # check defaults
    assert browser.find_by_name("shipping").value == "0"
    assert browser.find_by_name("payment").value == "0"

    move_to_element(browser, "select[name='shipping']")
    browser.select("shipping", shipping_method.pk)

    move_to_element(browser, "select[name='payment']")
    browser.select("payment", payment_method.pk)


def _test_confirm(browser):
    total = sum([decimal.Decimal(total_el.value) for total_el in browser.find_by_css("input[name='total']")])
    assert str(total) in browser.find_by_css(".order-footer h2").text, "order total is correct"
    click_element(browser, ".order-footer button")
    wait_until_appeared(browser, ".btn-danger")  # wait until the back button appears
    assert (
        len(browser.find_by_css("table tbody tr")) == 4
    ), "1 line items, 2 methods, 1 total line shown in confirmation table"
    # click confirm
    click_element(browser, ".btn-success")
    wait_until_appeared(browser, "#details-section")
    assert Order.objects.count() == 1, "order created"
