# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os
import pytest
import selenium
import time
from django.utils.translation import activate

from shuup.admin.signals import object_created
from shuup.core.models import Category, Product
from shuup.testing.browser_utils import (
    click_element,
    initialize_admin_browser_test,
    move_to_element,
    wait_until_appeared,
    wait_until_condition,
    wait_until_disappeared,
)
from shuup.testing.factories import (
    get_default_product_type,
    get_default_sales_unit,
    get_default_shop,
    get_default_tax_class,
)
from shuup.utils.django_compat import reverse

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")
OBJECT_CREATED_LOG_IDENTIFIER = "object_created_signal_handled"


@pytest.mark.django_db
def test_product_create(browser, admin_user, live_server, settings):
    activate("en")
    shop = get_default_shop()
    get_default_product_type()
    get_default_sales_unit()
    get_default_tax_class()
    object_created.connect(
        _add_custom_product_created_message, sender=Product, dispatch_uid="object_created_signal_test"
    )
    initialize_admin_browser_test(browser, live_server, settings)
    original_size = browser.driver.get_window_size()
    browser.driver.set_window_size(1920, 1080)

    url = reverse("shuup_admin:shop_product.new")
    browser.visit("%s%s" % (live_server, url))
    wait_until_condition(browser, condition=lambda x: x.is_text_present("New shop product"))

    sku = "testsku"
    name = "Some product name"
    price_value = 10
    short_description = "short but gold"
    move_to_element(browser, "#id_base-sku")
    browser.fill("base-sku", sku)
    browser.fill("base-name__en", name)
    browser.fill("base-short_description__en", short_description)
    browser.fill("shop%s-default_price_value" % shop.pk, price_value)

    _add_primary_category(browser, shop)
    _add_additional_category(browser, shop)

    move_to_element(browser, "button[form='product_form']")
    try:
        click_element(browser, "button[form='product_form']")
        wait_until_appeared(browser, "div[class='message success']")
    except selenium.common.exceptions.WebDriverException as e:
        # TODO: Revise!
        # Give a product save second chance it seems that the save can
        # lag a little and the success message doesn't happen fast
        # enough every single time.
        click_element(browser, "button[form='product_form']")
        wait_until_appeared(browser, "div[class='message success']")
    product = Product.objects.filter(sku=sku).first()
    assert product.log_entries.filter(identifier=OBJECT_CREATED_LOG_IDENTIFIER).count() == 1
    object_created.disconnect(sender=Product, dispatch_uid="object_created_signal_test")
    shop_product = product.get_shop_instance(shop)
    assert shop_product.categories.count() == 2
    browser.driver.set_window_size(original_size["width"], original_size["height"])


def _add_custom_product_created_message(sender, object, **kwargs):
    assert sender == Product
    object.add_log_entry("Custom object created signal handled", identifier=OBJECT_CREATED_LOG_IDENTIFIER)


def _add_primary_category(browser, shop):
    assert Category.objects.count() == 0
    select_id = "id_shop%s-primary_category" % shop.pk
    move_to_element(browser, "#%s" % select_id, header_height=100)

    # Quick add new primary category
    wait_until_appeared(browser, "#id_shop%d-primary_category ~ .quick-add-btn a.btn" % shop.id)
    click_element(browser, "#id_shop%d-primary_category ~ .quick-add-btn a.btn" % shop.id)
    wait_until_appeared(browser, "#create-object-iframe")
    with browser.get_iframe("create-object-iframe") as iframe:
        wait_until_appeared(iframe, "input[name='base-name__en']")
        iframe.fill("base-name__en", "Test Category")
        _save_category(iframe)

    wait_until_condition(browser, condition=lambda x: not x.is_element_present_by_id("create-object-overlay"))
    check_category_count(browser, 1)
    wait_until_condition(browser, lambda x: len(x.find_by_css("#%s option" % select_id)) == 1)


def _add_additional_category(browser, shop):
    assert Category.objects.count() == 1
    select_id = "id_shop%s-categories" % shop.pk
    move_to_element(browser, "#%s" % select_id, header_height=100)

    # Quick add new additional category
    wait_until_condition(browser, lambda x: len(x.find_by_css("#%s option[selected='']" % select_id)) == 1)
    wait_until_appeared(browser, "#id_shop%d-primary_category ~ .quick-add-btn a.btn" % shop.id)
    click_element(browser, "#id_shop%d-primary_category ~ .quick-add-btn a.btn" % shop.id)
    wait_until_appeared(browser, "#create-object-iframe")
    with browser.get_iframe("create-object-iframe") as iframe:
        wait_until_appeared(iframe, "input[name='base-name__en']")
        iframe.fill("base-name__en", "Test Category 2")
        _save_category(iframe)

    wait_until_condition(browser, condition=lambda x: not x.is_element_present_by_id("create-object-overlay"))
    check_category_count(browser, 2)
    wait_until_condition(browser, lambda x: len(x.find_by_css("#%s option[selected='']" % select_id)) == 2)


def check_category_count(browser, target_count):
    wait_until_condition(browser, condition=lambda x: Category.objects.count() == target_count)


def _save_category(iframe):  # TODO: Revise! It seems that iframes are hard for Travis
    time.sleep(3)  # Let's just wait here to the iFrame to open fully (for Chrome and headless)
    wait_until_appeared(iframe, "button[form='category_form']")
    try:
        click_element(iframe, "button[form='category_form']")
    except selenium.common.exceptions.SessionNotCreatedException as e:
        click_element(iframe, "button[form='category_form']")
