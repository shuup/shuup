# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import inspect

from django.conf import settings
from django.core import urlresolvers
from django.core.exceptions import MiddlewareNotUsed
from django.utils.module_loading import import_string
from django.utils.translation import activate, get_language

from shuup.admin.shop_provider import set_shop
from shuup.admin.utils.tour import set_tour_complete
from shuup.core import cache
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
        current_language = get_language()

        try:
            mw_instance = mw_class()
        except MiddlewareNotUsed:
            continue

        for key, value in attrs.items():
            setattr(request, key, value)

        if hasattr(mw_instance, 'process_request'):
            mw_instance.process_request(request)

        activate(current_language)

    assert request.shop

    if not attrs.get("skip_session", False):
        frm = inspect.stack()[1]
        mod = inspect.getmodule(frm[0])
        if mod.__name__.startswith("shuup_tests.admin"):
            set_shop(request, request.shop)

    return request


def apply_view_middleware(request):
    """
    Apply all the `process_view` capable middleware configured
    into the given request.

    The logic is roughly copied from
    django.core.handlers.base.BaseHandler.get_response

    :param request: The request to massage.
    :type request: django.http.HttpRequest
    :return: The same request, massaged in-place.
    :rtype: django.http.HttpRequest
    """
    urlconf = getattr(request, 'urlconf', settings.ROOT_URLCONF)
    urlresolvers.set_urlconf(urlconf)
    resolver = urlresolvers.RegexURLResolver(r'^/', urlconf)
    resolver_match = resolver.resolve(request.path_info)
    callback, callback_args, callback_kwargs = resolver_match
    request.resolver_match = resolver_match

    for middleware_path in settings.MIDDLEWARE_CLASSES:
        mw_class = import_string(middleware_path)
        try:
            mw_instance = mw_class()
        except MiddlewareNotUsed:
            continue

        if hasattr(mw_instance, 'process_view'):
            mw_instance.process_view(request, callback, callback_args, callback_kwargs)

    return request


def apply_all_middleware(request, **attrs):
    """
    Apply all the `process_request` and `process_view` capable
    middleware configured into the given request.

    :param request: The request to massage.
    :type request: django.http.HttpRequest
    :param attrs: Additional attributes to set to the request after massage.
    :type attrs: dict
    :return: The same request, massaged in-place.
    :rtype: django.http.HttpRequest
    """
    request = apply_view_middleware(apply_request_middleware(request))
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


def initialize_admin_browser_test(browser, live_server, settings, username="admin", password="password",
                                  onboarding=False, language="en", shop=None, tour_complete=True):
    if not onboarding:
        settings.SHUUP_SETUP_WIZARD_PANE_SPEC = []
    activate("en")
    cache.clear()

    shop = shop or get_default_shop()

    if tour_complete:
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.get(username=username)
        set_tour_complete(shop, "dashboard", True, user)
        set_tour_complete(shop, "home", True, user)
        set_tour_complete(shop, "product", True, user)
        set_tour_complete(shop, "category", True, user)

    url = live_server + "/sa"
    browser.visit(url)
    browser.fill('username', username)
    browser.fill('password', password)
    browser.find_by_css(".btn.btn-primary.btn-lg.btn-block").first.click()

    if not onboarding:
        # set shop language to eng
        browser.find_by_id("dropdownMenu").click()
        browser.find_by_xpath('//a[@data-value="%s"]' % language).first.click()

    return browser
