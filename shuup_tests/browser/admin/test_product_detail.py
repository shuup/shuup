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

from shuup.testing.browser_utils import (
    click_element,
    initialize_admin_browser_test,
    wait_until_appeared,
    wait_until_condition,
)
from shuup.testing.factories import create_product, get_default_shop
from shuup.utils.django_compat import reverse

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.django_db
@pytest.mark.skipif(os.environ.get("SHUUP_TESTS_CI", "0") == "1", reason="Disable when run in CI.")
def test_product_detail(browser, admin_user, live_server, settings):
    shop = get_default_shop()
    product = create_product("test_sku", shop, default_price=10)
    initialize_admin_browser_test(browser, live_server, settings)

    url = reverse("shuup_admin:shop_product.edit", kwargs={"pk": product.get_shop_instance(shop).pk})
    browser.visit("%s%s" % (live_server, url))
    assert browser.find_by_id("id_base-sku").value == product.sku

    # Test product save
    new_sku = "some-new-sku"
    browser.find_by_id("id_base-sku").fill(new_sku)
    browser.execute_script("window.scrollTo(0,0)")
    time.sleep(0.5)  # Otherwise other elements are still in the way, obscuring
    click_element(browser, "button[form='product_form']")

    # Here saving the product seems to take some time occasionally so it
    # should be worth to wait until the save goes through
    wait_until_condition(browser, condition=lambda x: x.is_text_present("Product was edited"), timeout=50)

    product.refresh_from_db()
    check_product_name(browser, product, new_sku)

    # Test that toolbar action item is there
    dropdowns = browser.find_by_css(".btn.dropdown-toggle")
    for dropdown in dropdowns:
        if "Actions" in dropdown.text:
            dropdown.click()

    wait_until_appeared(browser, "a[href='#%s']" % product.sku)
    click_element(browser, "a[href='#%s']" % product.sku)

    # Make sure that the tabs are clickable in small devices
    original_size = browser.driver.get_window_size()
    browser.driver.set_window_size(480, 960)
    time.sleep(0.5)  # Otherwise other elements are still in the way, obscuring
    click_element(browser, "#product-images-section", header_height=960)
    click_element(browser, "#additional-details-section", header_height=960)
    browser.driver.set_window_size(original_size["width"], original_size["height"])


def check_product_name(browser, product, target_name):
    wait_until_condition(browser, condition=lambda x: product.sku == target_name)
