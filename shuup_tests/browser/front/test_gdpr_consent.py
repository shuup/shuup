# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os
import pytest

from shuup.gdpr.models import GDPRSettings
from shuup.testing.browser_utils import (
    click_element,
    initialize_front_browser_test,
    wait_until_appeared,
    wait_until_condition,
)
from shuup.testing.factories import get_default_shop
from shuup.utils.django_compat import reverse

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.django_db
def test_gdpr_consent(browser, live_server, settings):
    shop = get_default_shop()
    index_url = reverse("shuup:index")

    # create a GDPR setting for the shop
    shop_gdpr = GDPRSettings.get_for_shop(shop)
    shop_gdpr.cookie_banner_content = "my cookie banner content"
    shop_gdpr.cookie_privacy_excerpt = "my cookie privacyexcerpt"
    shop_gdpr.enabled = True
    shop_gdpr.save()  # Enable GDPR

    browser = initialize_front_browser_test(browser, live_server)
    browser.visit("%s%s" % (live_server, index_url))
    wait_until_appeared(browser, ".gdpr-consent-warn-bar")
    assert len(browser.find_by_css(".gdpr-consent-preferences")) == 1
    click_element(browser, "#agree-btn")

    wait_until_condition(browser, lambda x: len(x.find_by_css(".gdpr-consent-warn-bar")) == 0)
    wait_until_condition(browser, lambda x: len(x.find_by_css(".gdpr-consent-preferences")) == 0)
