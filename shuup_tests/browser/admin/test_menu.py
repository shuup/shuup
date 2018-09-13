# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os

import pytest

from shuup.testing.browser_utils import wait_until_condition, wait_until_appeared
from shuup.testing.factories import get_default_shop
from shuup.testing.utils import initialize_admin_browser_test

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.browser
@pytest.mark.djangodb
def test_menu(browser, admin_user, live_server, settings):
    get_default_shop()
    initialize_admin_browser_test(browser, live_server, settings)

    wait_until_condition(browser, lambda x: x.is_text_present("Welcome!"))
    wait_until_condition(browser, lambda x: x.is_text_present("Quicklinks"))
    browser.find_by_css(".quicklinks a").first.click()

    wait_until_appeared(browser, ".item-category.item-active")
    browser.find_by_css(".menu-list li a")[1].click()

    wait_until_condition(browser, lambda x: x.is_text_present("New shop product"))


@pytest.mark.browser
@pytest.mark.djangodb
def test_menu_small_device(browser, admin_user, live_server, settings):
    get_default_shop()

    browser.driver.set_window_size(480, 960)
    initialize_admin_browser_test(browser, live_server, settings)

    wait_until_appeared(browser, "#menu-button")
    browser.find_by_css("#menu-button").first.click()
    wait_until_condition(browser, lambda x: x.is_text_present("Quicklinks"))
    browser.find_by_css(".quicklinks a").first.click()

    wait_until_appeared(browser, ".item-category.item-active")
    browser.find_by_css(".menu-list li a")[1].click()

    wait_until_condition(browser, lambda x: x.is_text_present("New shop product"))
