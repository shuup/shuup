# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from importlib import import_module

from django.conf import settings
from django.http import HttpResponse

from shuup.utils.importing import load

_URLCONF_ERROR_HANDLERS = {}
HANDLER_ATTR_FMT = "handler%s"


class ErrorPageHandler(object):
    """
    A base class for error pages handling.
    """

    @classmethod
    def can_handle_error(cls, request, error_status):
        """
        Returns whether this object can handle the error.

        :rtype: bool
        """
        raise NotImplementedError(
            "Error! Not implemented: `ErrorPageHandler` -> `apply_for_product()`. Implement this method."
        )

    @classmethod
    def handle_error(cls, request, error_status):
        """
        Returns a response for the given request and error status.

        :rtype: django.http.HttpResponse
        """
        raise NotImplementedError(
            "Error! Not implemented: `ErrorPageHandler` -> `handle_error(). Implement this method.`"
        )


def make_error_view(error_status):
    """
    A factory of error views which tries to find a compatible error handler.
    If there is no handler that can do the job, use the Django's default or return a blank response.
    """

    def view(request, *args, **kwargs):
        handler_attr = HANDLER_ATTR_FMT % error_status

        # look for compatible error handlers
        for handler_spec in settings.SHUUP_ERROR_PAGE_HANDLERS_SPEC:
            handler = load(handler_spec)()

            # return a response for the error status
            if handler.can_handle_error(request, error_status):
                return handler.handle_error(request, error_status)

        # tries to use the default handler (set in django's root urlconf)
        # otherwise just a blank response
        fallback_handler = _URLCONF_ERROR_HANDLERS.get(handler_attr)
        if fallback_handler and callable(fallback_handler):
            return fallback_handler(request)
        else:
            return HttpResponse(status=error_status)

    return view


def install_error_handlers():
    """
    Install custom error handlers.
    Error handlers to be added are for errors 400, 403, 404, and 500.
    """

    root_urlconf_module = getattr(settings, "ROOT_URLCONF", None)

    if not root_urlconf_module:  # That's weird, but let's not crash here.
        return

    try:
        root_urlconf = import_module(root_urlconf_module)
    except ImportError:  # Also weird, but not worth a crash.
        return

    for error_status in (400, 403, 404, 500):
        handler_attr = HANDLER_ATTR_FMT % error_status

        # save the currenct handlers for fallbacks
        if hasattr(root_urlconf, handler_attr):
            _URLCONF_ERROR_HANDLERS[handler_attr] = getattr(root_urlconf, handler_attr)

        # overwrite the error handlers by ours
        setattr(root_urlconf, handler_attr, make_error_view(error_status))
