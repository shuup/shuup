# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os
import pytest
from django.core.management import call_command

from shuup.core.models import AnonymousContact, Product, Shop, Supplier
from shuup.testing.browser_utils import (
    click_element,
    initialize_admin_browser_test,
    wait_until_appeared,
    wait_until_condition,
)

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.django_db
def test_dev_onboarding(browser, admin_user, live_server, settings):
    Shop.objects.first().delete()  # Delete first shop created by test initializations
    call_command("shuup_init", *[], **{})
    shop = Shop.objects.first()
    assert not shop.maintenance_mode
    initialize_admin_browser_test(browser, live_server, settings, onboarding=True)

    browser.fill("address-first_name", "Matti")
    browser.fill("address-last_name", "Teppo")
    browser.fill("address-phone", "112")
    browser.fill("address-street", "Teststreet")
    browser.fill("address-postal_code", "20540")
    browser.fill("address-city", "Turku")

    click_element(browser, "#select2-id_address-country-container")
    wait_until_appeared(browser, "input.select2-search__field")
    browser.find_by_css("input.select2-search__field").first.value = "Finland"
    wait_until_appeared(browser, ".select2-results__option:not([aria-live='assertive'])")
    browser.execute_script('$($(".select2-results__option")[0]).trigger({type: "mouseup"})')
    click_element(browser, "button[name='next']")

    wait_until_condition(browser, lambda x: x.is_text_present("To start accepting payments right away"))
    click_element(browser, "div[data-name='manual_payment'] button[name='activate']")
    browser.fill("manual_payment-service_name", "Laskulle")
    click_element(browser, "button[name='next']")

    wait_until_condition(browser, lambda x: x.is_text_present("To start shipping products right away"))
    click_element(browser, "div[data-name='manual_shipping'] button[name='activate']")
    browser.fill("manual_shipping-service_name", "Kotiinkuljetus")
    click_element(browser, "button[name='next']")

    wait_until_condition(browser, lambda x: x.is_text_present("theme for your shop"))
    click_element(browser, "div[data-identifier='candy_pink'] button[data-theme='shuup.themes.classic_gray']")
    click_element(browser, "button[name='next']")

    wait_until_condition(browser, lambda x: x.is_text_present("initial content and configure"))
    click_element(browser, "button[name='next']")

    wait_until_condition(browser, lambda x: x.is_text_present("install some sample data"))
    browser.execute_script('document.getElementsByName("sample-categories")[0].checked=true')
    browser.execute_script('document.getElementsByName("sample-products")[0].checked=true')
    click_element(browser, "button[name='next']")

    wait_until_condition(browser, lambda x: x.is_text_present("Welcome to Shuup!"))

    click_element(browser, "input[value='Publish shop']")

    shop.refresh_from_db()
    assert not shop.maintenance_mode
    assert Product.objects.count() == 10
    supplier = Supplier.objects.first()
    customer = AnonymousContact()
    assert (
        len(
            [
                product
                for product in Product.objects.all()
                if product.get_shop_instance(shop).is_orderable(supplier, customer, 1)
            ]
        )
        == 10
    )
