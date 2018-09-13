# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os

import pytest

from shuup.testing.browser_utils import wait_until_condition
from shuup.testing.factories import get_default_shop
from shuup.testing.utils import initialize_admin_browser_test

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.browser
@pytest.mark.djangodb
def test_menu(browser, admin_user, live_server, settings):
    get_default_shop()
    initialize_admin_browser_test(browser, live_server, settings)

    browser.find_by_css(".menu-list li").first.click()
    wait_until_condition(browser, lambda x: x.is_text_present("New product"))


@pytest.mark.browser
@pytest.mark.djangodb
def test_menu_small_device(browser, admin_user, live_server, settings):
    get_default_shop()

    browser.driver.set_window_size(480, 960)
    initialize_admin_browser_test(browser, live_server, settings)

    # TODO: Revise next line! For some the logo blocks selenium with regular click.
    browser.execute_script('$("#menu-button").click()')
    wait_until_condition(browser, lambda x: x.is_text_present("Quicklinks"))
    browser.execute_script('document.getElementById("js-main-menu").scrollIntoView();')
    browser.find_by_css(".menu-list li").first.click()
    wait_until_condition(browser, lambda x: x.is_text_present("New product"))
