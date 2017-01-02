# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os

import pytest
from django.core.urlresolvers import reverse

from shuup import configuration
from shuup.testing.browser_utils import click_element
from shuup.testing.factories import create_product, get_default_shop
from shuup.testing.utils import initialize_admin_browser_test

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.browser
@pytest.mark.djangodb
def test_product_detail(browser, admin_user, live_server, settings):
    shop = get_default_shop()
    product = create_product("test_sku", shop, default_price=10)
    configuration.set(None, "shuup_product_tour_complete", True)
    initialize_admin_browser_test(browser, live_server, settings)

    url = reverse("shuup_admin:shop_product.edit", kwargs={"pk": product.get_shop_instance(shop).pk})
    browser.visit("%s%s" % (live_server, url))
    assert browser.find_by_id("id_base-sku").value == product.sku

    # Test product save
    new_sku = "some-new-sku"
    browser.find_by_id("id_base-sku").fill(new_sku)
    browser.execute_script("window.scrollTo(0,0)")
    click_element(browser, "button[form='product_form']")

    product.refresh_from_db()
    assert product.sku == new_sku

    # Test that toolbar action item is there
    dropdowns = browser.find_by_css(".btn.dropdown-toggle")
    for dropdown in dropdowns:
        if "Actions" in dropdown.text:
            dropdown.click()
    click_element(browser, "a[href='#%s']" % product.sku)

    # Make sure that the tabs is clickable in small devices
    browser.driver.set_window_size(480, 960)

    click_element(browser, "#product-images-section", header_height=320)
    click_element(browser, "#additional-details-section", header_height=320)
