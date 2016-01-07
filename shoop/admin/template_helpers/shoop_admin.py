# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

"""
This module is installed as the `shoop_admin` template function namespace.
"""

import itertools

from django.core.urlresolvers import NoReverseMatch, reverse
from django.middleware.csrf import get_token
from jinja2.utils import contextfunction

from shoop.admin import menu
from shoop.admin.breadcrumbs import Breadcrumbs
from shoop.admin.utils.urls import (
    get_model_url, manipulate_query_string, NoModelUrl
)

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


# TODO: Figure out a more extensible way to deal with this
BROWSER_URL_NAMES = {
    "media": "shoop_admin:media.browse",
    "product": "shoop_admin:product.list",
    "contact": "shoop_admin:contact.list",
}


def get_browser_urls():
    browser_urls = {}
    for name, urlname in BROWSER_URL_NAMES.items():
        try:
            browser_urls[name] = reverse(urlname)
        except NoReverseMatch:  # This may occur when a module is not available.
            browser_urls[name] = None
    return browser_urls


@contextfunction
def get_config(context):
    request = context["request"]
    url_name = None
    if getattr(request, "resolver_match", None):
        # This does not exist when testing views directly
        url_name = request.resolver_match.url_name

    qs = {"context": url_name}
    return {
        "searchUrl": manipulate_query_string(reverse("shoop_admin:search"), **qs),
        "menuUrl": manipulate_query_string(reverse("shoop_admin:menu"), **qs),
        "browserUrls": get_browser_urls(),
        "csrf": get_token(request)
    }


@contextfunction
def get_breadcrumbs(context):
    breadcrumbs = context.get("breadcrumbs")
    if breadcrumbs is None:
        breadcrumbs = Breadcrumbs.infer(context)
    return breadcrumbs


def model_url(model, kind="detail", default=None):
    """
    Get a model URL of the given kind for a model (instance or class).

    :param model: The model instance or class.
    :type model: django.db.Model
    :param kind: The URL kind to retrieve. See `get_model_url`.
    :type kind: str
    :param default: Default value to return if model URL retrieval fails. If None,
                    the `NoModelUrl` exception is (re)raised.
    :type default: str|None
    :return: URL string.
    :rtype: str
    """
    try:
        return get_model_url(model, kind)
    except NoModelUrl:
        if default is None:
            raise
        return default
