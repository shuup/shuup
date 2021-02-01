# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import inspect

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.utils.module_loading import import_string
from django.utils.translation import activate, get_language

from shuup.admin import shop_provider
from shuup.utils.django_compat import (
    get_middleware_classes, RegexPattern, set_urlconf, URLResolver
)


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
    for middleware_path in get_middleware_classes():
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
            shop_provider.set_shop(request, request.shop)

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
    set_urlconf(urlconf)

    resolver = URLResolver(RegexPattern(r'^/'), urlconf)
    resolver_match = resolver.resolve(request.path_info)
    callback, callback_args, callback_kwargs = resolver_match
    request.resolver_match = resolver_match

    for middleware_path in get_middleware_classes():
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
