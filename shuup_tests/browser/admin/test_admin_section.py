# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import os

import pytest
from shuup.testing.utils import initialize_admin_browser_test


pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.browser
@pytest.mark.djangodb
def test_browser_admin_login(browser, admin_user, live_server):
    initialize_admin_browser_test(browser, live_server)
    assert browser.is_text_present("Active customers")  # login was successful
    browser.visit(live_server + "/sa/orders")
    assert browser.is_text_present("Orders")
