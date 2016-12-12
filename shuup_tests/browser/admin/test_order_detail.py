# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import os

import pytest
from django.core.urlresolvers import reverse
from django.utils.translation import activate

from shuup.core.models import OrderStatus
from shuup.testing.browser_utils import (
    click_element, wait_until_appeared, wait_until_condition
)
from shuup.testing.factories import create_empty_order, get_default_shop
from shuup.testing.utils import initialize_admin_browser_test

pytestmark = pytest.mark.skipif(os.environ.get("SHUUP_BROWSER_TESTS", "0") != "1", reason="No browser tests run.")


@pytest.mark.browser
@pytest.mark.djangodb
def test_product_detail(browser, admin_user, live_server, settings):
    activate(settings.PARLER_DEFAULT_LANGUAGE_CODE)
    shop = get_default_shop()
    order = create_empty_order(shop=shop)
    order.save()
    initialize_admin_browser_test(browser, live_server, settings)
    url = reverse("shuup_admin:order.detail", kwargs={"pk": order.pk})
    browser.visit("%s%s" % (live_server, url))
    wait_until_condition(browser, condition=lambda x: x.is_text_present("Order %s" % order.pk))

    set_status(browser, order, OrderStatus.objects.get_default_processing())
    assert order.can_set_complete()
    set_status(browser, order, OrderStatus.objects.get_default_complete())


def set_status(browser, order, status):
    click_element(browser, "button.set-status-button")
    form_action = reverse("shuup_admin:order.set-status", kwargs={"pk": order.pk})
    click_element(browser, "button[formaction='%s'][value='%s']" % (form_action, status.pk))
    wait_until_appeared(browser, "div[class='message success']")
    wait_until_condition(browser, condition=lambda x: x.is_text_present("Order %s" % order.pk))
    order.refresh_from_db()
    assert order.status.pk == status.pk
