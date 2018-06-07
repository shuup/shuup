# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os
import pytest

from django.conf import settings
from django.test import override_settings

from shuup.core.models import OrderStatus, OrderStatusRole
from shuup.testing.browser_utils import (
    click_element, move_to_element, wait_until_appeared,
    wait_until_disappeared,
    wait_until_condition)
from shuup.testing.factories import (
    create_product, get_default_payment_method, get_default_shipping_method,
    get_default_shop, get_default_supplier
)
from shuup.testing.utils import initialize_front_browser_test
from shuup.utils.importing import clear_load_cache

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


def create_orderable_product(name, sku, price):
    supplier = get_default_supplier()
    shop = get_default_shop()
    product = create_product(sku=sku, shop=shop, supplier=supplier, default_price=price, name=name)
    return product


@pytest.mark.browser
@pytest.mark.djangodb
def test_browser_checkout_horizontal(browser, live_server, settings):
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
    wait_until_condition(browser, lambda x: x.is_text_present("Welcome to Default!"))
    wait_until_condition(browser, lambda x: x.is_text_present("Newest Products"))
    wait_until_condition(browser, lambda x: x.is_text_present(product_name))

    click_element(browser, "#product-%s" % product.pk)  # open product from product list
    click_element(browser, "#add-to-cart-button-%s" % product.pk)  # add product to basket

    wait_until_appeared(browser, ".cover-wrap")
    wait_until_disappeared(browser, ".cover-wrap")

    click_element(browser, "#navigation-basket-partial")  # open upper basket navigation menu
    click_element(browser, "a[href='/basket/']")  # click the link to basket in dropdown
    wait_until_condition(browser, lambda x: x.is_text_present("Shopping cart"))  # we are in basket page
    wait_until_condition(browser, lambda x: x.is_text_present(product_name))  # product is in basket

    click_element(browser, "a[href='/checkout/']") # click link that leads to checkout

    customer_name = "Test Tester"
    customer_street = "Test Street"
    customer_city = "Test City"
    customer_region = "CA"
    customer_country = "US"

    # Fill all necessary information
    browser.fill("billing-name", customer_name)
    browser.fill("billing-street", customer_street)
    browser.fill("billing-city", customer_city)
    browser.select("billing-country", customer_country)
    wait_until_appeared(browser, "select[name='billing-region_code']")
    browser.select("billing-region_code", customer_region)

    click_element(browser, "#addresses button[type='submit']")  # This shouldn't submit since missing required fields

    # Fill rest of the fields
    browser.fill("shipping-name", customer_name)
    browser.fill("shipping-street", customer_street)
    browser.fill("shipping-city", customer_city)
    browser.select("shipping-country", customer_country)

    click_element(browser, "#addresses button[type='submit']")
    wait_until_condition(browser, lambda x: x.is_text_present("Checkout: Shipping & Payment"))

    wait_until_condition(browser, lambda x: x.is_text_present(sm.name))  # shipping method name is present
    wait_until_condition(browser, lambda x: x.is_text_present(pm.name))  # payment method name is present

    click_element(browser, ".btn.btn-primary.btn-lg.pull-right")  # click "continue" on methods page

    wait_until_condition(browser, lambda x: x.is_text_present("Checkout: Confirmation"))  # we are indeed in confirmation page

    # See that all expected texts are present
    wait_until_condition(browser, lambda x: x.is_text_present(product_name))
    wait_until_condition(browser, lambda x: x.is_text_present(sm.name))
    wait_until_condition(browser, lambda x: x.is_text_present(pm.name))
    wait_until_condition(browser, lambda x: x.is_text_present("Delivery"))
    wait_until_condition(browser, lambda x: x.is_text_present("Billing"))

    # check that user information is available
    wait_until_condition(browser, lambda x: x.is_text_present(customer_name))
    wait_until_condition(browser, lambda x: x.is_text_present(customer_street))
    wait_until_condition(browser, lambda x: x.is_text_present(customer_city))
    wait_until_condition(browser, lambda x: x.is_text_present("United States"))

    browser.execute_script('document.getElementById("id_accept_terms").checked=true')  # click accept terms
    click_element(browser, ".btn.btn-primary.btn-lg")  # click "place order"

    wait_until_condition(browser, lambda x: x.is_text_present("Thank you for your order!"))  # order succeeded


@pytest.mark.urls('shuup.testing.single_page_checkout_test_urls')
@pytest.mark.browser
@pytest.mark.djangodb
def test_browser_checkout_vertical(browser, live_server, settings): 
    with override_settings(SHUUP_CHECKOUT_VIEW_SPEC=("shuup.front.views.checkout:SinglePageCheckoutView")):
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
        wait_until_condition(browser, lambda x: x.is_text_present("Welcome to Default!"))
        wait_until_condition(browser, lambda x: x.is_text_present("Newest Products"))
        wait_until_condition(browser, lambda x: x.is_text_present(product_name))

        click_element(browser, "#product-%s" % product.pk)  # open product from product list
        click_element(browser, "#add-to-cart-button-%s" % product.pk)  # add product to basket

        wait_until_appeared(browser, ".cover-wrap")
        wait_until_disappeared(browser, ".cover-wrap")

        click_element(browser, "#navigation-basket-partial")  # open upper basket navigation menu
        click_element(browser, "a[href='/basket/']")  # click the link to basket in dropdown
        wait_until_condition(browser, lambda x: x.is_text_present("Shopping cart"))  # we are in basket page
        wait_until_condition(browser, lambda x: x.is_text_present(product_name))  # product is in basket

        click_element(browser, "a[href='/checkout/']") # click link that leads to checkout
        wait_until_appeared(browser, "h4.panel-title")
        customer_name = "Test Tester"
        customer_street = "Test Street"
        customer_city = "Test City"
        customer_region = "CA"
        customer_country = "US"

        # Fill all necessary information
        browser.fill("billing-name", customer_name)
        browser.fill("billing-street", customer_street)
        browser.fill("billing-city", customer_city)
        browser.select("billing-country", customer_country)
        wait_until_appeared(browser, "select[name='billing-region_code']")
        browser.select("billing-region_code", customer_region)

        click_element(browser, "#addresses button[type='submit']")

        click_element(browser, "#addresses button[type='submit']")  # This shouldn't submit since missing required fields

        # Fill rest of the fields
        browser.fill("shipping-name", customer_name)
        browser.fill("shipping-street", customer_street)
        browser.fill("shipping-city", customer_city)
        browser.select("shipping-country", customer_country)

        click_element(browser, "#addresses button[type='submit']")
        wait_until_condition(browser, lambda x: x.is_text_present("Shipping & Payment"))

        wait_until_condition(browser, lambda x: x.is_text_present(sm.name))  # shipping method name is present
        wait_until_condition(browser, lambda x: x.is_text_present(pm.name))  # payment method name is present

        click_element(browser, ".btn.btn-primary.btn-lg.pull-right")  # click "continue" on methods page

        wait_until_condition(browser, lambda x: x.is_text_present("Confirmation"))  # we are indeed in confirmation page

        # See that all expected texts are present
        wait_until_condition(browser, lambda x: x.is_text_present(product_name))
        wait_until_condition(browser, lambda x: x.is_text_present(sm.name))
        wait_until_condition(browser, lambda x: x.is_text_present(pm.name))
        wait_until_condition(browser, lambda x: x.is_text_present("Delivery"))
        wait_until_condition(browser, lambda x: x.is_text_present("Billing"))

        # check that user information is available
        wait_until_condition(browser, lambda x: x.is_text_present(customer_name))
        wait_until_condition(browser, lambda x: x.is_text_present(customer_street))
        wait_until_condition(browser, lambda x: x.is_text_present(customer_city))
        wait_until_condition(browser, lambda x: x.is_text_present("United States"))

        browser.execute_script('document.getElementById("id_accept_terms").checked=true')  # click accept terms
        click_element(browser, ".btn.btn-primary.btn-lg")  # click "place order"

        wait_until_condition(browser, lambda x: x.is_text_present("Thank you for your order!"))  # order succeeded
