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

from shuup.testing.browser_utils import initialize_admin_browser_test, wait_until_appeared, wait_until_condition
from shuup.testing.factories import get_default_shop
from shuup.utils.django_compat import reverse

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.django_db
@pytest.mark.skipif(os.environ.get("SHUUP_TESTS_CI", "0") == "1", reason="Disable when run in CI.")
def test_login_logout(browser, admin_user, live_server, settings):
    get_default_shop()
    initialize_admin_browser_test(browser, live_server, settings)
    browser.visit("%s%s" % (live_server, "/sa/logout"))
    wait_until_condition(browser, lambda x: x.is_text_present("You have been securely logged out."))
