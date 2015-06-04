# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

"""
This module is installed as the `shoop_admin` template function namespace.
"""

from django.core.urlresolvers import reverse, NoReverseMatch
from django.middleware.csrf import get_token
from jinja2.utils import contextfunction
from shoop.admin import menu
from shoop.admin.breadcrumbs import Breadcrumbs
from shoop.admin.utils.urls import get_model_url, manipulate_query_string
import itertools

__all__ = ["get_menu_entry_categories", "get_front_url", "get_config", "model_url"]


@contextfunction
def get_menu_entry_categories(context):
    return menu.get_menu_entry_categories(request=context["request"])


@contextfunction
def get_menu_entries(context):
    return sorted(itertools.chain(*(
        c.entries
        for c
        in menu.get_menu_entry_categories(request=context["request"]).values()
    )), key=(lambda m: m.text))


@contextfunction
def get_front_url(context):
    front_url = context.get("front_url")
    if not front_url:
        try:
            front_url = reverse("shoop:index")
        except NoReverseMatch:
            front_url = None
    return front_url


@contextfunction
def get_config(context):
    request = context["request"]
    url_name = None
    if getattr(request, "resolver_match", None):
        # This does not exist when testing views directly
        url_name = request.resolver_match.url_name

    try:
        media_browse_url = reverse("shoop_admin:media.browse")
    except NoReverseMatch:  # This may occur when the media module is not available.
        media_browse_url = None

    qs = {"context": url_name}
    return {
        "searchUrl": manipulate_query_string(reverse("shoop_admin:search"), **qs),
        "menuUrl": manipulate_query_string(reverse("shoop_admin:menu"), **qs),
        "mediaBrowserUrl": media_browse_url,
        "csrf": get_token(request)
    }


@contextfunction
def get_breadcrumbs(context):
    breadcrumbs = context.get("breadcrumbs")
    if breadcrumbs is None:
        breadcrumbs = Breadcrumbs.infer(context)
    return breadcrumbs


def model_url(model):
    return get_model_url(model)
