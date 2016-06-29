# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from importlib import import_module

from django.conf import settings
from django.shortcuts import render


def make_error_view(status, template_name=None):
    if not template_name:
        template_name = "shuup/front/errors/%s.jinja" % status

    def view(request, *args, **kwargs):
        return render(request=request, template_name=template_name, status=status)

    return view


def install_error_handlers():
    """
    Install custom error handlers.

    Error handlers to be added are for errors 400, 403, 404, and 500.

    Error handlers will be injected only if:
    * `settings.SHUUP_FRONT_INSTALL_ERROR_HANDLERS` is `True`
    * `settings.ROOT_URLCONF` doesn't already contain the handler
    """

    root_urlconf_module = getattr(settings, "ROOT_URLCONF", None)

    if not root_urlconf_module:  # That's weird, but let's not crash here.
        return

    try:
        root_urlconf = import_module(root_urlconf_module)
    except ImportError:  # Also weird, but not worth a crash.
        return

    for status in (400, 403, 404, 500):
        handler_attr = "handler%s" % status
        if not hasattr(root_urlconf, handler_attr):
            setattr(root_urlconf, handler_attr, make_error_view(status))
