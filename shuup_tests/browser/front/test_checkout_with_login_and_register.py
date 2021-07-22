# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os
import pytest
import time
from django.test.utils import override_settings

from shuup.core import cache
from shuup.core.models import Order, OrderStatus, OrderStatusRole, PersonContact, Product
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
from shuup.utils.django_compat import reverse

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


def create_orderable_product(name, sku, price):
    supplier = get_default_supplier()
    shop = get_default_shop()
    product = create_product(sku=sku, shop=shop, supplier=supplier, default_price=price, name=name)
    return product


@override_settings(SHUUP_REGISTRATION_REQUIRES_ACTIVATION=False)
@pytest.mark.urls("shuup.testing.checkout_with_login_and_register_urls")
@pytest.mark.django_db
def test_checkout_with_login_and_register(browser, live_server, reindex_catalog):
    cache.clear()  # Avoid caches from past tests
    # initialize
    product_name = "Test Product"
    get_default_shop()
    get_default_payment_method()
    get_default_shipping_method()
    product = create_orderable_product(product_name, "test-123", price=100)
    reindex_catalog()
    OrderStatus.objects.create(identifier="initial", role=OrderStatusRole.INITIAL, name="initial", default=True)

    # Initialize test and go to front page
    browser = initialize_front_browser_test(browser, live_server)

    wait_until_condition(browser, lambda x: x.is_text_present("Welcome to Default!"))
    navigate_to_checkout(browser, product)

    # Let's assume that after addresses the checkout is normal
    wait_until_condition(browser, lambda x: x.is_text_present("Checkout Method"))
    guest_ordering_test(browser, live_server)

    test_username = "test_username"
    test_email = "test@example.com"
    test_password = "test_password"
    wait_until_condition(browser, lambda x: x.is_text_present("Checkout Method"))
    register_test(browser, live_server, test_username, test_email, test_password)

    wait_until_condition(browser, lambda x: x.is_text_present("Checkout Method"))
    login_and_finish_up_the_checkout(browser, live_server, test_username, test_email, test_password)


@override_settings(SHUUP_REGISTRATION_REQUIRES_ACTIVATION=False)
@pytest.mark.urls("shuup.testing.single_page_checkout_with_login_and_register_conf")
@pytest.mark.django_db
@pytest.mark.skipif(os.environ.get("SHUUP_TESTS_CI", "0") == "1", reason="Disable when run in CI.")
def test_single_page_checkout_with_login_and_register(browser, live_server, reindex_catalog):
    cache.clear()  # Avoid caches from past tests

    # initialize
    product_name = "Test Product"
    get_default_shop()
    get_default_payment_method()
    get_default_shipping_method()
    product = create_orderable_product(product_name, "test-123", price=100)
    reindex_catalog()
    OrderStatus.objects.create(identifier="initial", role=OrderStatusRole.INITIAL, name="initial", default=True)

    # Initialize test and go to front page
    browser = initialize_front_browser_test(browser, live_server)

    wait_until_condition(browser, lambda x: x.is_text_present("Welcome to Default!"))
    navigate_to_checkout(browser, product)

    # Let's assume that after addresses the checkout is normal
    wait_until_condition(browser, lambda x: x.is_text_present("Checkout Method"))
    test_username = "test_username"
    test_email = "test@example.com"
    test_password = "test_password"
    register_test(browser, live_server, test_username, test_email, test_password)

    login_and_finish_up_the_checkout(browser, live_server, test_username, test_email, test_password)


def navigate_to_checkout(browser, product):
    wait_until_condition(browser, lambda x: x.is_text_present("Newest Products"))
    wait_until_condition(browser, lambda x: x.is_text_present(product.name))

    click_element(browser, "#product-%s" % product.pk)  # open product from product list
    click_element(browser, "#add-to-cart-button-%s" % product.pk)  # add product to basket

    time.sleep(1)

    click_element(browser, "#navigation-basket-partial")  # open upper basket navigation menu
    click_element(browser, "a[href='/basket/']")  # click the link to basket in dropdown
    time.sleep(1)

    wait_until_condition(browser, lambda x: x.is_text_present("Shopping cart"))  # we are in basket page
    wait_until_condition(browser, lambda x: x.is_text_present(product.name))  # product is in basket

    click_element(browser, "a[href='/checkout/']")  # click link that leads to checkout

    time.sleep(1)


def guest_ordering_test(browser, live_server):
    browser.fill("login-username", "test-username")
    click_element(browser, "button[name='login']")  # Shouldn't submit
    browser.fill("login-password", "test-password")
    click_element(browser, "button[name='login']")
    wait_until_condition(browser, lambda x: x.is_text_present("Please enter a correct username and password."))
    wait_until_appeared(browser, "div.alert.alert-danger")

    click_element(browser, "button[data-id='id_checkout_method_choice-register']")
    click_element(browser, "button[data-id='id_checkout_method_choice-register'] + .dropdown-menu li:nth-child(1) a")
    click_element(browser, "div.clearfix button.btn.btn-primary.btn-lg.pull-right")
    wait_until_condition(browser, lambda x: x.is_text_present("Checkout: Addresses"))
    url = reverse("shuup:checkout", kwargs={"phase": "checkout_method"})
    browser.visit("%s%s" % (live_server, url))


def register_test(browser, live_server, test_username, test_email, test_password):
    click_element(browser, "button[data-id='id_checkout_method_choice-register']")
    click_element(browser, "button[data-id='id_checkout_method_choice-register'] + .dropdown-menu li:nth-child(2) a")
    click_element(browser, "div.clearfix button.btn.btn-primary.btn-lg.pull-right")
    wait_until_condition(browser, lambda x: x.is_text_present("Register"))

    browser.find_by_id("id_registration_for_username").fill(test_username)
    browser.find_by_id("id_registration_for_email").fill(test_email)
    browser.find_by_id("id_registration_for_password1").fill(test_password)
    browser.find_by_id("id_registration_for_password2").fill("typo-%s" % test_password)
    click_element(browser, "div.clearfix button.btn.btn-primary.btn-lg.pull-right")
    wait_until_appeared(browser, "div.form-group.passwordinput.required.has-error")

    browser.find_by_id("id_registration_for_password1").fill(test_password)
    browser.find_by_id("id_registration_for_password2").fill(test_password)
    click_element(browser, "div.clearfix button.btn.btn-primary.btn-lg.pull-right")

    wait_until_condition(browser, lambda x: x.is_text_present("Addresses"))
    # Reload here just in case since there might have been reload with JS
    # which might cause issues with tests since the elements is in cache
    browser.reload()

    # Log out and go back to checkout choice phase
    click_element(browser, "div.top-nav i.menu-icon.fa.fa-user")
    click_element(browser, "a[href='/logout/']")

    # Ensure that the language is still english. It seems that the language might change
    # during the logout.
    browser.find_by_id("language-changer").click()
    browser.find_by_xpath('//a[@class="language"]').first.click()

    # There is no products on basket anymore so let's add one
    product = Product.objects.first()
    product_url = reverse("shuup:product", kwargs={"pk": product.pk, "slug": product.slug})
    browser.visit("%s%s" % (live_server, product_url))
    click_element(browser, "#add-to-cart-button-%s" % product.pk)  # add product to basket

    wait_until_appeared(browser, ".cover-wrap")
    wait_until_disappeared(browser, ".cover-wrap")

    browser.visit("%s%s" % (live_server, "/checkout/"))


def login_and_finish_up_the_checkout(browser, live_server, test_username, test_email, test_password):
    fields = browser.driver.find_elements_by_name("login-username")
    # there should be only a single username field
    assert len(fields) == 1

    browser.fill("login-username", test_email)
    browser.fill("login-password", test_password)
    click_element(browser, "button[name='login']")

    wait_until_condition(browser, lambda x: x.is_text_present("Addresses"), timeout=100)
    # Reload here just in case since there might have been reload with JS
    # which might cause issues with tests since the elements is in cache
    browser.reload()

    # This should be first order upcoming
    assert Order.objects.count() == 0

    # Fnish the checkout
    customer_name = "Test Tester"
    customer_street = "Test Street"
    customer_city = "Test City"
    customer_region = "CA"
    customer_country = "US"

    # Fill all necessary information
    browser.fill("billing-name", customer_name)
    browser.fill("billing-street", customer_street)
    browser.fill("billing-city", customer_city)
    wait_until_appeared(browser, "#id_billing-region")
    browser.select("billing-country", customer_country)
    wait_until_disappeared(browser, "#id_billing-region")
    wait_until_appeared(browser, "select[name='billing-region_code']")
    browser.select("billing-region_code", customer_region)

    click_element(browser, "#addresses button[type='submit']")  # Shouldn't submit since required fields

    browser.fill("shipping-name", customer_name)
    browser.fill("shipping-street", customer_street)
    browser.fill("shipping-city", customer_city)
    wait_until_appeared(browser, "#id_shipping-region")
    browser.select("shipping-country", customer_country)
    wait_until_disappeared(browser, "#id_shipping-region")
    wait_until_appeared(browser, "select[name='shipping-region_code']")

    click_element(browser, "#addresses button[type='submit']")
    wait_until_condition(browser, lambda x: x.is_text_present("Shipping & Payment"))

    pm = get_default_payment_method()
    sm = get_default_shipping_method()

    wait_until_condition(browser, lambda x: x.is_text_present(sm.name))  # shipping method name is present
    wait_until_condition(browser, lambda x: x.is_text_present(pm.name))  # payment method name is present

    click_element(browser, ".btn.btn-primary.btn-lg.pull-right")  # click "continue" on methods page

    wait_until_condition(browser, lambda x: x.is_text_present("Confirmation"))  # we are indeed in confirmation page
    product = Product.objects.first()

    # See that all expected texts are present
    wait_until_condition(browser, lambda x: x.is_text_present(product.name))
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

    # Let's make sure the order now has a customer
    assert Order.objects.count() == 1
    order = Order.objects.first()
    assert order.customer == PersonContact.objects.filter(user__username=test_username).first()
    assert order.customer.name == customer_name
    assert order.customer.default_shipping_address is not None
    assert order.customer.default_billing_address is not None
    assert order.customer.user.username == test_username
