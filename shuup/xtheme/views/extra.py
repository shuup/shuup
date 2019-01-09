# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.exceptions import ImproperlyConfigured
from django.core.signals import setting_changed
from django.http.response import HttpResponseNotFound

from shuup.xtheme._theme import get_current_theme

_VIEW_CACHE = {}


def clear_view_cache(**kwargs):
    _VIEW_CACHE.clear()


setting_changed.connect(clear_view_cache, dispatch_uid="shuup.xtheme.views.extra.clear_view_cache")


def _get_view_by_name(theme, view_name):
    view = theme.get_view(view_name)
    if hasattr(view, "as_view"):  # Handle CBVs
        view = view.as_view()
    if view and not callable(view):
        raise ImproperlyConfigured("View %r not callable" % view)
    return view


def get_view_by_name(theme, view_name):
    if not theme:
        return None
    cache_key = (theme.identifier, view_name)
    if cache_key not in _VIEW_CACHE:
        view = _get_view_by_name(theme, view_name)
        _VIEW_CACHE[cache_key] = view
    else:
        view = _VIEW_CACHE[cache_key]
    return view


def extra_view_dispatch(request, view):
    """
    Dispatch to an Xtheme extra view.

    :param request: A request
    :type request: django.http.HttpRequest
    :param view: View name
    :type view: str
    :return: A response of some ilk
    :rtype: django.http.HttpResponse
    """
    theme = get_current_theme(request.shop)
    view_func = get_view_by_name(theme, view)
    if not view_func:
        msg = "%s/%s: Not found" % (getattr(theme, "identifier", None), view)
        return HttpResponseNotFound(msg)
    return view_func(request)
