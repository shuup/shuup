# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.template.response import TemplateResponse
from django.utils import importlib


def make_error_view(status, template_name=None):
    if not template_name:
        template_name = "shoop/front/errors/%s.jinja" % status

    def view(request, *args, **kwargs):
        return TemplateResponse(request, template_name, status=status)

    return view


def install_error_handlers():
    """
    Install custom error handlers.

    Error handlers to be added are for errors 400, 403, 404, and 500.

    Error handlers will be injected only if:
    * `settings.SHOOP_FRONT_INSTALL_ERROR_HANDLERS` is `True`
    * `settings.ROOT_URLCONF` doesn't already contain the handler
    """
    root_urlconf = importlib.import_module(settings.ROOT_URLCONF)

    for status in (400, 403, 404, 500):
        handler_attr = "handler%s" % status
        if not hasattr(root_urlconf, handler_attr):
            setattr(root_urlconf, handler_attr, make_error_view(status))
