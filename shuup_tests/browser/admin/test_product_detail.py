# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import os
import pytest

from django.core.urlresolvers import reverse

from shuup.testing.factories import create_product, get_default_shop
from shuup.testing.utils import initialize_admin_browser_test


pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.browser
@pytest.mark.djangodb
def test_product_detail(browser, admin_user, live_server):
    shop = get_default_shop()
    product = create_product("test_sku", shop)
    initialize_admin_browser_test(browser, live_server)

    url = reverse("shuup_admin:product.edit", kwargs={"pk": product.pk})
    browser.visit("%s%s" % (live_server, url))
    assert browser.find_by_id("id_base-sku").value == product.sku

    # Test product save
    new_sku = "some-new-sku"
    browser.find_by_id("id_base-sku").fill(new_sku)
    browser.execute_script("window.scrollTo(0,0)")
    browser.find_by_xpath('//button[@form="product_form"]').first.click()

    product.refresh_from_db()
    assert product.sku == new_sku

    # Test that toolbar action item is there
    dropdowns = browser.find_by_css(".btn.dropdown-toggle")
    for dropdown in dropdowns:
        if "Actions" in dropdown.text:
            dropdown.click()
    browser.find_by_xpath('//a[@href="#%s"]' % product.sku).first.click()
