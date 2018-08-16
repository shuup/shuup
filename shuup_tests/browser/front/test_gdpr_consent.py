# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os

import pytest
from django.core.urlresolvers import reverse

from shuup.gdpr.models import GDPRSettings
from shuup.testing.browser_utils import (
    click_element, wait_until_appeared
)
from shuup.testing.factories import get_default_shop
from shuup.testing.utils import initialize_front_browser_test

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")

@pytest.mark.browser
def test_gdpr_consent(browser, live_server, settings):
    browser = initialize_front_browser_test(browser, live_server)

    shop = get_default_shop()
    index_url = reverse("shuup:index")

    # create a GDPR setting for the shop
    shop_gdpr = GDPRSettings.get_for_shop(shop)
    shop_gdpr.cookie_banner_content = "my cookie banner content"
    shop_gdpr.cookie_privacy_excerpt = "my cookie privacyexcerpt"
    shop_gdpr.enabled = True
    shop_gdpr.save() # Enable GDPR

    browser.visit("%s%s" % (live_server, index_url))
    wait_until_appeared(browser, ".gdpr-consent-warn-bar")
    assert (len(browser.find_by_css(".gdpr-consent-preferences")) == 1)
    click_element(browser, "#agree-btn")

    assert len(browser.find_by_css(".gdpr-consent-warn-bar")) == 0
    assert len(browser.find_by_css(".gdpr-consent-preferences")) == 0
