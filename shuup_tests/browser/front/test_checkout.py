# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import os

import pytest
from shuup.core.models import OrderStatus, OrderStatusRole
from shuup.testing.browser_utils import (
    wait_until_appeared, wait_until_disappeared
)
from shuup.testing.factories import (
    create_product, get_default_payment_method, get_default_shipping_method,
    get_default_shop, get_default_supplier
)
from shuup.testing.utils import initialize_front_browser_test


pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


def create_orderable_product(name, sku, price):
    supplier = get_default_supplier()
    shop = get_default_shop()
    product = create_product(sku=sku, shop=shop, supplier=supplier, default_price=price, name=name)
    return product


@pytest.mark.browser
@pytest.mark.djangodb
def test_browser_checkout(browser, live_server, settings):
    # initialize
    product_name = "Test Product"
    get_default_shop()
    pm = get_default_payment_method()
    sm = get_default_shipping_method()
    product = create_orderable_product(product_name, "test-123", price=100)
    OrderStatus.objects.create(
        identifier="initial",
        role=OrderStatusRole.INITIAL,
        name="initial",
        default=True
    )

    # initialize test and go to front page
    browser = initialize_front_browser_test(browser, live_server)

    # check that front page actually loaded
    assert browser.is_text_present("Welcome to Default!")
    assert browser.is_text_present("Newest Products")
    assert browser.is_text_present(product_name)

    browser.find_by_id("product-%s" % product.pk).click()  # open product from product list
    browser.find_by_id("add-to-cart-button").click()  # add product to basket

    wait_until_appeared(browser, ".cover-wrap")
    wait_until_disappeared(browser, ".cover-wrap")

    browser.find_by_id("navigation-basket-partial").click()  # open upper basket navigation menu
    browser.find_link_by_href("/basket/").first.click()  # click the link to basket in dropdown
    assert browser.is_text_present("Shopping cart")  # we are in basket page
    assert browser.is_text_present(product_name)  # product is in basket

    browser.find_link_by_href("/checkout/").first.click()  # click link that leads to checkout

    customer_name = "Test Tester"
    customer_street = "Test Street"
    customer_city = "Test City"
    customer_country = "US"

    # Fill all necessary information
    browser.fill("billing-name", customer_name)
    browser.fill("billing-street", customer_street)
    browser.fill("billing-city", customer_city)
    browser.select("billing-country", customer_country)

    browser.find_by_css("#addresses button[type='submit']").first.click()  # click "continue"

    assert browser.is_text_present("There were errors on submitted form fields. Please check them and try again.")

    # Fill the errors
    browser.fill("shipping-name", customer_name)
    browser.fill("shipping-street", customer_street)
    browser.fill("shipping-city", customer_city)
    browser.select("shipping-country", customer_country)

    browser.find_by_css("#addresses button[type='submit']").first.click()  # click "continue"
    assert browser.is_text_present("Checkout: Shipping & Payment")

    assert browser.is_text_present(sm.name)  # shipping method name is present
    assert browser.is_text_present(pm.name)  # payment method name is present

    browser.find_by_css(".btn.btn-primary.btn-lg.pull-right").first.click()  # click "continue" on methods page

    assert browser.is_text_present("Checkout: Confirmation")  # we are indeed in confirmation page

    # See that all expected texts are present
    assert browser.is_text_present(product_name)
    assert browser.is_text_present(sm.name)
    assert browser.is_text_present(pm.name)
    assert browser.is_text_present("Delivery")
    assert browser.is_text_present("Billing")

    # check that user information is available
    assert browser.is_text_present(customer_name)
    assert browser.is_text_present(customer_street)
    assert browser.is_text_present(customer_city)
    assert browser.is_text_present("United States")

    browser.execute_script('document.getElementById("id_accept_terms").checked=true')  # click accept terms
    browser.find_by_css(".btn.btn-primary.btn-lg").first.click()  # click "place order"

    browser.is_text_present("Thank you for your order!")  # order succeeded
