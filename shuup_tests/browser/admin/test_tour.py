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
from selenium.common.exceptions import ElementNotInteractableException

from shuup.admin.utils.tour import is_tour_complete
from shuup.testing import factories
from shuup.testing.browser_utils import (
    click_element,
    initialize_admin_browser_test,
    move_to_element,
    wait_until_condition,
)

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.django_db
def test_dashbord_tour(browser, admin_user, live_server, settings):
    shop = factories.get_default_shop()
    shop2 = factories.get_shop(identifier="shop2")
    admin_user_2 = factories.create_random_user(is_staff=True, is_superuser=True)
    admin_user_2.set_password("password")
    admin_user_2.save()

    shop.staff_members.add(admin_user)
    shop.staff_members.add(admin_user_2)

    # test with admin_user 1
    initialize_admin_browser_test(browser, live_server, settings, shop=shop, tour_complete=False)
    wait_until_condition(browser, lambda x: x.is_text_present("Welcome!"))
    wait_until_condition(browser, lambda x: x.is_text_present("Quicklinks"))
    wait_until_condition(browser, lambda x: x.is_element_present_by_css("#menu-button"))
    wait_until_condition(browser, lambda x: x.is_text_present("This is the dashboard for your store."), timeout=30)
    wait_until_condition(browser, lambda x: x.is_element_present_by_css(".shepherd-button.btn-primary"))
    click_element(browser, ".shepherd-button.btn-primary")
    wait_until_condition(browser, lambda x: not x.is_element_present_by_css(".shepherd-button"))
    wait_until_condition(browser, lambda x: is_tour_complete(shop, "dashboard", admin_user))

    browser.visit(live_server + "/logout")
    browser.visit(live_server + "/sa")

    # test with admin_user 2
    initialize_admin_browser_test(
        browser, live_server, settings, shop=shop, tour_complete=False, username=admin_user_2.username
    )
    wait_until_condition(browser, lambda x: x.is_text_present("Welcome!"))
    wait_until_condition(browser, lambda x: x.is_element_present_by_css("#menu-button"))
    wait_until_condition(browser, lambda x: x.is_text_present("This is the dashboard for your store."), timeout=30)
    wait_until_condition(browser, lambda x: x.is_element_present_by_css(".shepherd-button.btn-primary"))
    click_element(browser, ".shepherd-button.btn-primary")
    wait_until_condition(browser, lambda x: not x.is_element_present_by_css(".shepherd-button"))
    wait_until_condition(browser, lambda x: is_tour_complete(shop, "dashboard", admin_user_2))

    # check whether the tour is shown again
    browser.visit(live_server + "/sa")
    wait_until_condition(browser, lambda x: not x.is_text_present("This is the dashboard for your store."))

    assert is_tour_complete(shop2, "dashboard", admin_user) is False
    assert is_tour_complete(shop2, "dashboard", admin_user_2) is False


@pytest.mark.django_db
@pytest.mark.skipif(os.environ.get("SHUUP_TESTS_CI", "0") == "1", reason="Disable when run in CI.")
def test_home_tour(browser, admin_user, live_server, settings):
    shop = factories.get_default_shop()
    shop2 = factories.get_shop(identifier="shop2")
    admin_user_2 = factories.create_random_user(is_staff=True, is_superuser=True)
    admin_user_2.set_password("password")
    admin_user_2.save()

    shop.staff_members.add(admin_user)
    shop.staff_members.add(admin_user_2)

    for user in [admin_user, admin_user_2]:
        initialize_admin_browser_test(browser, live_server, settings, username=user.username, tour_complete=False)
        wait_until_condition(browser, lambda x: x.is_text_present("Welcome!"))
        browser.visit(live_server + "/sa/home")

        wait_until_condition(browser, lambda x: x.is_text_present("Hi, new shop owner!"), timeout=30)
        wait_until_condition(browser, lambda x: x.is_element_present_by_css(".shepherd-button.btn-primary"))
        click_element(browser, ".shepherd-button.btn-primary")

        category_targets = [
            ".shepherd-enabled[data-target-id='category-1'",
            ".shepherd-enabled[data-target-id='category-2'",
            ".shepherd-enabled[data-target-id='category-3'",
            ".shepherd-enabled[data-target-id='category-5'",
            ".shepherd-enabled[data-target-id='category-9'",
            ".shepherd-enabled[data-target-id='category-4'",
            ".shepherd-enabled[data-target-id='category-6'",
            ".shepherd-enabled[data-target-id='category-7'",
            ".shepherd-enabled[data-target-id='category-8'",
            ".shepherd-enabled#site-search",
            ".shepherd-enabled.shop-btn.visit-store",
        ]
        for target in category_targets:
            wait_until_condition(browser, lambda x: x.is_element_present_by_css(target))
            move_to_element(browser, ".shepherd-button.btn-primary")
            browser.find_by_css(".shepherd-button.btn-primary").last.click()

        wait_until_condition(browser, lambda x: x.is_text_present("We're done!"), timeout=30)
        move_to_element(browser, ".shepherd-button.btn-primary")
        browser.find_by_css(".shepherd-button.btn-primary").last.click()
        wait_until_condition(browser, lambda x: is_tour_complete(shop, "home", user))

        # check whether the tour is shown again
        browser.visit(live_server + "/sa/home")
        wait_until_condition(browser, lambda x: not x.is_text_present("Hi, new shop owner!"))

        browser.visit(live_server + "/logout")
        browser.visit(live_server + "/sa")

        wait_until_condition(browser, lambda x: not x.is_text_present("Hi, new shop owner!"))

        assert is_tour_complete(shop2, "home", user) is False


@pytest.mark.django_db
def test_product_tour(browser, admin_user, live_server, settings):
    shop = factories.get_default_shop()
    shop2 = factories.get_shop(identifier="shop2")
    admin_user_2 = factories.create_random_user(is_staff=True, is_superuser=True)
    admin_user_2.set_password("password")
    admin_user_2.save()
    product = factories.get_default_product()
    shop_product = product.get_shop_instance(shop)

    shop.staff_members.add(admin_user)
    shop.staff_members.add(admin_user_2)

    for user in [admin_user, admin_user_2]:
        initialize_admin_browser_test(browser, live_server, settings, username=user.username, tour_complete=False)
        wait_until_condition(browser, lambda x: x.is_text_present("Welcome!"))
        browser.visit(live_server + "/sa/products/%d/" % shop_product.pk)

        wait_until_condition(browser, lambda x: x.is_text_present(shop_product.product.name))
        # as this is added through javascript, add an extra timeout
        wait_until_condition(browser, lambda x: x.is_text_present("You are adding a product."), timeout=30)
        wait_until_condition(browser, lambda x: x.is_element_present_by_css(".shepherd-button.btn-primary"))
        click_element(browser, ".shepherd-button.btn-primary")

        category_targets = [
            "a.shepherd-enabled[href='#basic-information-section']",
            "a.shepherd-enabled[href='#additional-details-section']",
            "a.shepherd-enabled[href='#manufacturer-section']",
            "a.shepherd-enabled[href*='-additional-section']",
            "a.shepherd-enabled[href='#product-media-section']",
            "a.shepherd-enabled[href='#product-images-section']",
            "a.shepherd-enabled[href='#contact-group-pricing-section']",
            "a.shepherd-enabled[href='#contact-group-discount-section']",
        ]

        # Scroll top before starting to click. For some reason the first
        # item is not found without this. For Firefox or Chrome the browser
        # does not do any extra scroll which could hide the first item.
        # Steps are scrollTo false on purpose since the scrollTo true is the
        # config which does not work in real world.
        browser.execute_script("window.scrollTo(0,0)")
        for target in category_targets:
            time.sleep(0.25)

            try:
                wait_until_condition(browser, lambda x: x.is_element_present_by_css(target))
                browser.find_by_css(".shepherd-button.btn-primary").last.click()
            except ElementNotInteractableException:
                move_to_element(browser, ".shepherd-button.btn-primary")
                wait_until_condition(browser, lambda x: x.is_element_present_by_css(target))
                browser.find_by_css(".shepherd-button.btn-primary").last.click()

        wait_until_condition(browser, lambda x: is_tour_complete(shop, "product", user))

        # check whether the tour is shown again
        browser.visit(live_server + "/sa/products/%d/" % shop_product.pk)
        wait_until_condition(browser, lambda x: not x.is_text_present("You are adding a product."), timeout=20)

        assert is_tour_complete(shop2, "product", user) is False

        browser.visit(live_server + "/logout")
        browser.visit(live_server + "/sa")


@pytest.mark.django_db
def test_category_tour(browser, admin_user, live_server, settings):
    shop = factories.get_default_shop()
    shop2 = factories.get_shop(identifier="shop2")
    admin_user_2 = factories.create_random_user(is_staff=True, is_superuser=True)
    admin_user_2.set_password("password")
    admin_user_2.save()

    shop.staff_members.add(admin_user)
    shop.staff_members.add(admin_user_2)

    for user in [admin_user, admin_user_2]:
        initialize_admin_browser_test(browser, live_server, settings, username=user.username, tour_complete=False)
        wait_until_condition(browser, lambda x: x.is_text_present("Welcome!"))
        browser.visit(live_server + "/sa/categories/new")

        wait_until_condition(browser, lambda x: x.is_text_present("Add a new product category"), timeout=30)
        wait_until_condition(browser, lambda x: x.is_element_present_by_css(".shepherd-button.btn-primary"))
        click_element(browser, ".shepherd-button.btn-primary")
        wait_until_condition(browser, lambda x: not x.is_element_present_by_css(".shepherd-button"))
        wait_until_condition(browser, lambda x: is_tour_complete(shop, "category", user))

        # check whether the tour is shown again
        browser.visit(live_server + "/sa/categories/new")
        wait_until_condition(browser, lambda x: not x.is_text_present("Add a new product category"))

        browser.visit(live_server + "/logout")
        browser.visit(live_server + "/sa")

        assert is_tour_complete(shop2, "category", user) is False
