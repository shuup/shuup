# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

"""
This module is installed as the `shuup_admin` template function namespace.
"""

import itertools
from django.conf import settings
from django.middleware.csrf import get_token
from functools import lru_cache
from jinja2.utils import contextfunction

from shuup import configuration
from shuup.admin import menu
from shuup.admin.breadcrumbs import Breadcrumbs
from shuup.admin.shop_provider import get_shop
from shuup.admin.supplier_provider import get_supplier
from shuup.admin.utils.menu import is_menu_open
from shuup.admin.utils.urls import NoModelUrl, manipulate_query_string
from shuup.apps.provides import get_provide_objects
from shuup.core.models import Shop
from shuup.core.telemetry import is_telemetry_enabled
from shuup.utils import django_compat
from shuup.utils.django_compat import NoReverseMatch, force_text, reverse
from shuup.utils.importing import cached_load

__all__ = ["get_menu_entry_categories", "get_front_url", "get_config", "model_url"]


@contextfunction
def get_quicklinks(context):
    request = context["request"]
    if request.GET.get("context") == "home":
        return []
    return menu.get_quicklinks(request=context["request"])


@contextfunction
def get_menu_entry_categories(context):
    return menu.get_menu_entry_categories(request=context["request"])


@lru_cache()
def get_all_target_urls(request, target_url, breadcrumbs):
    breadcrumbs_entries = breadcrumbs.get_entries(request) or [] if breadcrumbs else []
    return [entry.url for entry in breadcrumbs_entries] + [target_url]


@contextfunction
def is_menu_category_active(context, category, target_url, breadcrumbs=None):
    def does_identifier_match(always_active_identifier):
        return force_text(category.identifier) == force_text(always_active_identifier)

    identifiers = settings.SHUUP_ALWAYS_ACTIVE_MENU_CATEGORY_IDENTIFIERS
    if any([identifier for identifier in identifiers if does_identifier_match(identifier)]):
        return True

    all_target_urls = get_all_target_urls(context["request"], target_url, breadcrumbs)
    return any([entry for entry in category.entries if entry.url in all_target_urls])


@contextfunction
def is_menu_item_active(context, entry_url, target_url, breadcrumbs=None):
    return bool(entry_url in get_all_target_urls(context["request"], target_url, breadcrumbs))


@contextfunction
def get_menu_entries(context):
    return sorted(
        itertools.chain(*(c.entries for c in menu.get_menu_entry_categories(request=context["request"]).values())),
        key=(lambda m: m.text),
    )


@contextfunction
def get_front_url(context):
    return cached_load("SHUUP_ADMIN_NAVIGATION_GET_FRONT_URL_SPEC")(context)


@contextfunction
def get_support_id(context):
    support_id = None
    if is_telemetry_enabled():
        support_id = configuration.get(None, "shuup_support_id")
    return support_id


def get_browser_urls(request):
    browser_urls = {}

    for admin_browser_config_provider in get_provide_objects("admin_browser_config_provider"):
        browser_urls.update(admin_browser_config_provider.get_browser_urls(request))

    reversed_browser_urls = {}
    for name, urlname in browser_urls.items():
        try:
            if isinstance(urlname, (tuple, list)):
                urlname, args, kwargs = urlname
                reversed_browser_urls[name] = reverse(urlname, args=args, kwargs=kwargs)
            else:
                reversed_browser_urls[name] = reverse(urlname)
        except NoReverseMatch:  # This may occur when a module is not available.
            reversed_browser_urls[name] = None

    return reversed_browser_urls


def get_settings(request):
    admin_settings = {}
    for admin_browser_config_provider in get_provide_objects("admin_browser_config_provider"):
        admin_settings.update(admin_browser_config_provider.get_gettings(request))
    return admin_settings


@contextfunction
def get_config(context):
    request = context["request"]
    url_name = None
    if getattr(request, "resolver_match", None):
        # This does not exist when testing views directly
        url_name = request.resolver_match.url_name

    qs = {"context": url_name}
    return {
        "searchUrl": manipulate_query_string(reverse("shuup_admin:search"), **qs),
        "menuUrl": manipulate_query_string(reverse("shuup_admin:menu"), **qs),
        "browserUrls": get_browser_urls(request),
        "csrf": get_token(request),
        "docsPage": settings.SHUUP_ADMIN_MERCHANT_DOCS_PAGE,
        "menuOpen": is_menu_open(request),
        "settings": get_settings(request),
    }


@contextfunction
def get_docs_help_url(context, page=""):
    """
    Returns the merchant documentation page.

    :param str|None page: the specific page to return.
        If nothing is passed, the root page will be returned.
    """
    if page:
        from six.moves.urllib.parse import urljoin

        return urljoin(settings.SHUUP_ADMIN_MERCHANT_DOCS_PAGE, page)
    return settings.SHUUP_ADMIN_MERCHANT_DOCS_PAGE


@contextfunction
def get_breadcrumbs(context):
    breadcrumbs = context.get("breadcrumbs")
    if breadcrumbs is None:
        breadcrumbs = Breadcrumbs.infer(context)
    return breadcrumbs


@contextfunction
def model_url(context, model, kind="detail", default=None, **kwargs):
    """
    Get a model URL of the given kind for a model (instance or class).

    :param context: Jinja rendering context
    :type context: jinja2.runtime.Context
    :param model: The model instance or class.
    :type model: django.db.Model
    :param kind: The URL kind to retrieve. See `get_model_url`.
    :type kind: str
    :param default: Default value to return if model URL retrieval fails.
    :type default: str
    :return: URL string.
    :rtype: str
    """
    user = context.get("user")
    try:
        request = context.get("request")
        shop = get_shop(request) if request else None
        admin_model_url_resolvers = get_provide_objects("admin_model_url_resolver")

        for resolver in admin_model_url_resolvers:
            url = resolver(model, kind=kind, user=user, shop=shop, **kwargs)
            if url:
                return url
    except NoModelUrl:
        return default


@contextfunction
def get_shop_count(context):
    """
    Return the number of shops accessible by the currently logged in user
    """
    request = context["request"]
    if not (request and not django_compat.is_anonymous(request.user)):
        return 0
    return Shop.objects.get_for_user(request.user).count()


@contextfunction
def get_admin_shop(context):
    return get_shop(context["request"])


@contextfunction
def is_multishop_enabled(context):
    return settings.SHUUP_ENABLE_MULTIPLE_SHOPS is True


@contextfunction
def get_current_language(context):
    from django.utils.translation import get_language

    return get_language()


@contextfunction
def get_admin_supplier(context):
    return get_supplier(context["request"])


@contextfunction
def is_multiple_suppliers_enabled(context):
    return settings.SHUUP_ENABLE_MULTIPLE_SUPPLIERS is True


@contextfunction
def get_logout_url(context):
    request = context["request"]

    def get_url(url):
        try:
            return reverse(url)
        except NoReverseMatch:
            return None

    stop_impersonate_url = None
    if "impersonator_user_id" in request.session:
        stop_impersonate_url = get_url("shuup_admin:stop-impersonating-staff")

    return stop_impersonate_url if stop_impersonate_url else get_url("shuup_admin:logout") or "/logout"


def is_authenticated(user):
    return django_compat.is_authenticated(user)
