# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os
import pytest
from django.test import override_settings

from shuup.core.models import OrderStatus, OrderStatusRole
from shuup.testing.browser_utils import (
    click_element,
    initialize_front_browser_test,
    wait_until_appeared,
    wait_until_condition,
    wait_until_disappeared,
)
from shuup.testing.factories import (
    create_product,
    get_default_payment_method,
    get_default_shipping_method,
    get_default_shop,
    get_default_supplier,
    get_payment_method,
    get_shipping_method,
)
from shuup.utils.django_compat import reverse

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


def create_orderable_product(name, sku, price):
    supplier = get_default_supplier()
    shop = get_default_shop()
    product = create_product(sku=sku, shop=shop, supplier=supplier, default_price=price, name=name)
    return product


@pytest.mark.django_db
def test_browser_checkout_horizontal(browser, live_server, reindex_catalog):
    # initialize
    product_name = "Test Product"
    get_default_shop()
    pm = get_default_payment_method()
    sm = get_default_shipping_method()
    product = create_orderable_product(product_name, "test-123", price=100)
    reindex_catalog()
    OrderStatus.objects.create(identifier="initial", role=OrderStatusRole.INITIAL, name="initial", default=True)

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

    click_element(browser, "a[href='/checkout/']")  # click link that leads to checkout

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

    wait_until_condition(
        browser, lambda x: x.is_text_present("Checkout: Confirmation")
    )  # we are indeed in confirmation page

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


@pytest.mark.urls("shuup.testing.single_page_checkout_test_urls")
@pytest.mark.django_db
def test_browser_checkout_vertical(browser, live_server, reindex_catalog):
    with override_settings(SHUUP_CHECKOUT_VIEW_SPEC=("shuup.front.views.checkout:SinglePageCheckoutView")):
        # initialize
        product_name = "Test Product"
        get_default_shop()
        pm = get_default_payment_method()
        sm = get_default_shipping_method()
        product = create_orderable_product(product_name, "test-123", price=100)
        reindex_catalog()
        OrderStatus.objects.create(identifier="initial", role=OrderStatusRole.INITIAL, name="initial", default=True)

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

        click_element(browser, "a[href='/checkout/']")  # click link that leads to checkout
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

        click_element(
            browser, "#addresses button[type='submit']"
        )  # This shouldn't submit since missing required fields

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


@pytest.mark.parametrize("delete_method", ["shipping", "payment"])
@pytest.mark.django_db
def test_browser_checkout_disable_methods(browser, live_server, reindex_catalog, delete_method):
    product_name = "Test Product"
    get_default_shop()

    payment_method = get_default_payment_method()
    shipping_method = get_default_shipping_method()

    product = create_orderable_product(product_name, "test-123", price=100)
    reindex_catalog()
    OrderStatus.objects.create(identifier="initial", role=OrderStatusRole.INITIAL, name="initial", default=True)

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

    click_element(browser, "a[href='/checkout/']")  # click link that leads to checkout

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
    wait_until_condition(browser, lambda x: x.is_text_present(payment_method.name))
    wait_until_condition(browser, lambda x: x.is_text_present(shipping_method.name))

    browser.find_by_css("input[name='shipping_method'][value='%d']" % shipping_method.pk).first.click()
    browser.find_by_css("input[name='payment_method'][value='%d']" % payment_method.pk).first.click()

    click_element(browser, ".btn.btn-primary.btn-lg.pull-right")  # click "continue" on methods page
    wait_until_condition(
        browser, lambda x: x.is_text_present("Checkout: Confirmation")
    )  # we are indeed in confirmation page

    if delete_method == "payment":
        payment_method.delete()
    else:
        shipping_method.delete()

    click_element(browser, "a[href='/checkout/methods/']")

    wait_until_condition(browser, lambda x: x.is_text_present("Checkout: Shipping & Payment"))

    if delete_method == "payment":
        wait_until_condition(browser, lambda x: x.is_text_present("No method is available."))
        wait_until_condition(browser, lambda x: not x.is_text_present(payment_method.name))
        wait_until_condition(browser, lambda x: x.is_text_present(shipping_method.name))
    else:
        wait_until_condition(browser, lambda x: x.is_text_present("No method is available."))
        wait_until_condition(browser, lambda x: x.is_text_present(payment_method.name))
        wait_until_condition(browser, lambda x: not x.is_text_present(shipping_method.name))
