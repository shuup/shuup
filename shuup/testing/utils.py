# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.utils.module_loading import import_string
from django.utils.translation import activate

from shuup import configuration
from shuup.testing.factories import get_default_shop


def apply_request_middleware(request, **attrs):
    """
    Apply all the `process_request` capable middleware configured
    into the given request.

    :param request: The request to massage.
    :type request: django.http.HttpRequest
    :param attrs: Additional attributes to set after massage.
    :type attrs: dict
    :return: The same request, massaged in-place.
    :rtype: django.http.HttpRequest
    """
    for middleware_path in settings.MIDDLEWARE_CLASSES:
        mw_class = import_string(middleware_path)
        try:
            mw_instance = mw_class()
        except MiddlewareNotUsed:
            continue

        if hasattr(mw_instance, 'process_request'):
            mw_instance.process_request(request)
    for key, value in attrs.items():
        setattr(request, key, value)
    return request


def initialize_front_browser_test(browser, live_server):
    activate("en")
    get_default_shop()
    url = live_server + "/"
    browser.visit(url)
    # set shop language to eng
    browser.find_by_id("language-changer").click()
    browser.find_by_xpath('//a[@class="language"]').first.click()
    return browser


def initialize_admin_browser_test(browser, live_server, settings, username="admin", password="password"):
    settings.SHUUP_SETUP_WIZARD_PANE_SPEC = []
    activate("en")
    get_default_shop()
    configuration.set(None, "shuup_dashboard_tour_complete", True)
    url = live_server + "/sa"
    browser.visit(url)
    browser.fill('username', username)
    browser.fill('password', password)
    browser.find_by_css(".btn.btn-primary.btn-lg.btn-block").first.click()
    # set shop language to eng
    browser.find_by_id("dropdownMenu").click()
    browser.find_by_xpath('//a[@data-value="en"]').first.click()

    return browser
