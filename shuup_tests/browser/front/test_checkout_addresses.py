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
)

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


def create_orderable_product(name, sku, price):
    supplier = get_default_supplier()
    shop = get_default_shop()
    product = create_product(sku=sku, shop=shop, supplier=supplier, default_price=price, name=name)
    return product


@pytest.mark.django_db
def test_browser_checkout_addresses_horizontal(browser, live_server, reindex_catalog):
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

    customer_city1 = "Los Angeles"
    customer_city2 = "Blumenau"
    customer_city3 = "Vancouver"

    customer_region1 = "CA"
    customer_region2 = "SC"
    customer_region3 = "BC"

    customer_country1 = "US"
    customer_country2 = "BR"
    customer_country3 = "CA"

    # Fill all billing address fields with USA address
    browser.fill("billing-name", customer_name)
    browser.fill("billing-street", customer_street)
    browser.fill("billing-city", customer_city1)
    browser.select("billing-country", customer_country1)
    wait_until_appeared(browser, "select[name='billing-region_code']")
    browser.select("billing-region_code", customer_region1)

    # Fill all shipping address fields - Brazil address
    browser.fill("shipping-name", customer_name)
    browser.fill("shipping-street", customer_street)
    browser.fill("shipping-city", customer_city2)
    browser.select("shipping-country", customer_country2)
    wait_until_appeared(browser, "select[name='shipping-region_code']")
    browser.select("shipping-region_code", customer_region2)

    # Actually, click to send to billing address (copy billing to shipping)
    browser.find_by_css("label[for='same_as_billing']").first.click()

    # check whether fields are disable and the values are equals
    wait_until_condition(browser, lambda x: x.find_by_name("shipping-region_code").has_class("disabled"))
    wait_until_condition(browser, lambda x: x.find_by_name("shipping-country").has_class("disabled"))
    billing_country = browser.find_by_name("billing-country").first
    shipping_country = browser.find_by_name("shipping-country").first
    wait_until_appeared(browser, "select[name='billing-region_code']")
    wait_until_appeared(browser, "select[name='shipping-region_code']")
    billing_region_code = browser.find_by_name("billing-region_code").first
    shipping_region_code = browser.find_by_name("shipping-region_code").first
    assert billing_country.value == shipping_country.value
    assert billing_region_code.value == shipping_region_code.value

    # Actually, send to Canada
    browser.find_by_css("label[for='same_as_billing']").first.click()
    wait_until_condition(browser, lambda x: not x.find_by_name("shipping-region_code").has_class("disabled"))
    wait_until_condition(browser, lambda x: not x.find_by_name("shipping-country").has_class("disabled"))
    browser.fill("shipping-city", customer_city3)
    browser.select("shipping-country", customer_country3)
    wait_until_appeared(browser, "select[name='shipping-region_code']")
    browser.select("shipping-region_code", customer_region3)

    # continue
    click_element(browser, "#addresses button[type='submit']")

    wait_until_condition(browser, lambda x: x.is_text_present("Checkout: Shipping & Payment"))
    wait_until_condition(browser, lambda x: x.is_text_present(sm.name))  # shipping method name is present
    wait_until_condition(browser, lambda x: x.is_text_present(pm.name))  # payment method name is present

    # back to address phase, we want to send to Brazil nstead
    address_link = browser.find_by_text("1. Addresses")
    address_link.click()

    # all values must be there with correct saved values
    billing_country = browser.find_by_name("billing-country").first
    wait_until_appeared(browser, "select[name='billing-region_code']")
    billing_region_code = browser.find_by_name("billing-region_code").first
    shipping_country = browser.find_by_name("shipping-country").first
    wait_until_appeared(browser, "select[name='shipping-region_code']")
    shipping_region_code = browser.find_by_name("shipping-region_code").first
    assert billing_country.value == customer_country1
    assert billing_region_code.value == customer_region1
    assert shipping_country.value == customer_country3
    assert shipping_region_code.value == customer_region3

    # Fill shipping with Brazil and Billing with Canada
    browser.fill("shipping-city", customer_city2)
    browser.select("shipping-country", customer_country2)
    wait_until_appeared(browser, "select[name='shipping-region_code']")
    browser.select("shipping-region_code", customer_region2)

    browser.fill("billing-city", customer_city3)
    browser.select("billing-country", customer_country3)
    wait_until_appeared(browser, "select[name='billing-region_code']")
    browser.select("billing-region_code", customer_region3)

    # continue
    click_element(browser, "#addresses button[type='submit']")
    wait_until_condition(browser, lambda x: x.is_text_present("Checkout: Shipping & Payment"))

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
    wait_until_condition(browser, lambda x: x.is_text_present(customer_city2))
    wait_until_condition(browser, lambda x: x.is_text_present(customer_city3))
    wait_until_condition(browser, lambda x: x.is_text_present("Canada"))
    wait_until_condition(browser, lambda x: x.is_text_present("Brazil"))

    browser.execute_script('document.getElementById("id_accept_terms").checked=true')  # click accept terms
    click_element(browser, ".btn.btn-primary.btn-lg")
    wait_until_condition(browser, lambda x: x.is_text_present("Thank you for your order!"))


@pytest.mark.urls("shuup.testing.single_page_checkout_test_urls")
@pytest.mark.django_db
def test_browser_checkout_addresses_vertical(browser, live_server, reindex_catalog):
    with override_settings(SHUUP_CHECKOUT_VIEW_SPEC=("shuup.front.views.checkout:SinglePageCheckoutView")):
        # initialize
        product_name = "Test Product"
        get_default_shop()
        get_default_payment_method()
        get_default_shipping_method()
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

        customer_city1 = "Los Angeles"
        customer_city2 = "Chiedo"

        customer_region1 = "CA"
        customer_region2 = "My Region Name"

        customer_country1 = "US"
        customer_country2 = "AR"  # Doesn't have region codes

        # Fill all billing address fields with USA address
        browser.fill("billing-name", customer_name)
        browser.fill("billing-street", customer_street)
        browser.fill("billing-city", customer_city1)
        browser.select("billing-country", customer_country1)
        wait_until_appeared(browser, "select[name='billing-region_code']")
        browser.select("billing-region_code", customer_region1)

        # Click to send to billing address (copy billing to shipping)
        browser.find_by_css("label[for='same_as_billing']").first.click()

        # continue
        click_element(browser, "#addresses button[type='submit']")

        wait_until_condition(browser, lambda x: x.is_text_present("Shipping & Payment"))
        # continue on methods page
        click_element(browser, ".btn.btn-primary.btn-lg.pull-right")
        wait_until_condition(browser, lambda x: x.is_text_present("Confirmation"))

        # See that all expected texts are present
        wait_until_condition(browser, lambda x: x.is_text_present(customer_name))
        wait_until_condition(browser, lambda x: x.is_text_present(customer_street))
        wait_until_condition(browser, lambda x: x.is_text_present(customer_city1))
        wait_until_condition(browser, lambda x: x.is_text_present("United States"))

        # back to address phase, we want to send to Argentina
        browser.find_by_css("a[data-phase='addresses']").first.click()

        # all values must be there with correct saved values
        billing_country = browser.find_by_name("billing-country").first
        wait_until_appeared(browser, "select[name='billing-region_code']")
        billing_region_code = browser.find_by_name("billing-region_code").first
        shipping_country = browser.find_by_name("shipping-country").first
        wait_until_appeared(browser, "select[name='shipping-region_code']")
        shipping_region_code = browser.find_by_name("shipping-region_code").first
        assert billing_country.value == customer_country1
        assert billing_region_code.value == customer_region1
        assert shipping_country.value == customer_country1
        assert shipping_region_code.value == customer_region1

        # same_as_billing is not checked
        assert not browser.find_by_css("label[for='same_as_billing']").first.checked

        # click on same as billing twice, so we copy and clean the field, just to try messing
        browser.find_by_css("label[for='same_as_billing']").first.click()
        browser.find_by_css("label[for='same_as_billing']").first.click()

        # region field should be enabled
        wait_until_condition(browser, lambda x: not x.find_by_name("shipping-region_code").has_class("disabled"))

        # Fill all shipping address fields - Argentina address
        browser.fill("shipping-name", customer_name)
        browser.fill("shipping-street", customer_street)
        browser.fill("shipping-city", customer_city2)
        browser.select("shipping-country", customer_country2)
        browser.fill("shipping-region", customer_region2)

        # continue
        click_element(browser, "#addresses button[type='submit']")
        wait_until_condition(browser, lambda x: x.is_text_present("Shipping & Payment"))
        # continue
        click_element(browser, ".btn.btn-primary.btn-lg.pull-right")
        wait_until_condition(browser, lambda x: x.is_text_present("Confirmation"))

        wait_until_condition(browser, lambda x: x.is_text_present(customer_name))
        wait_until_condition(browser, lambda x: x.is_text_present(customer_street))
        wait_until_condition(browser, lambda x: x.is_text_present(customer_city1))
        wait_until_condition(browser, lambda x: x.is_text_present(customer_city2))
        wait_until_condition(browser, lambda x: x.is_text_present(customer_region1))
        wait_until_condition(browser, lambda x: x.is_text_present(customer_region2))
        wait_until_condition(browser, lambda x: x.is_text_present("Argentina"))
        wait_until_condition(browser, lambda x: x.is_text_present("United States"))

        browser.execute_script('document.getElementById("id_accept_terms").checked=true')  # click accept terms
        click_element(browser, ".btn.btn-primary.btn-lg")  # click "place order"

        wait_until_condition(browser, lambda x: x.is_text_present("Thank you for your order!"))  # order succeeded
