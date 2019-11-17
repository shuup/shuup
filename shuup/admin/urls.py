# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

import warnings

import django
import django.contrib.auth.views as auth_views
from django.conf.urls import url
from django.contrib.auth import logout as do_logout
from django.views.decorators.csrf import csrf_exempt
from django.views.i18n import set_language

from shuup.admin.module_registry import get_module_urls
from shuup.admin.utils.urls import admin_url, AdminRegexURLPattern
from shuup.admin.views.dashboard import DashboardView
from shuup.admin.views.edit import EditObjectView
from shuup.admin.views.home import HomeView
from shuup.admin.views.impersonate import stop_impersonating_staff
from shuup.admin.views.menu import MenuToggleView, MenuView
from shuup.admin.views.password import RequestPasswordView, ResetPasswordView
from shuup.admin.views.search import SearchView
from shuup.admin.views.select import MultiselectAjaxView
from shuup.admin.views.tour import TourView
from shuup.admin.views.wizard import WizardView
from shuup.utils.django_compat import is_anonymous
from shuup.utils.i18n import javascript_catalog_all
from shuup.utils.importing import cached_load


def login(request, **kwargs):
    if not is_anonymous(request.user) and request.method == "POST":  # We're logging in, so log out first
        do_logout(request)

    kwargs.setdefault("extra_context", {})["error"] = request.GET.get("error")
    if django.VERSION < (2, 0):
        return auth_views.login(
            request=request,
            authentication_form=cached_load("SHUUP_ADMIN_AUTH_FORM_SPEC"),
            **kwargs
        )
    else:
        return auth_views.LoginView.as_view(
            form_class=cached_load("SHUUP_ADMIN_AUTH_FORM_SPEC"),
            **kwargs
        )(request)


def get_urls():
    urls = []
    urls.extend(get_module_urls())

    urls.extend([
        admin_url(r'^$', DashboardView.as_view(), name='dashboard', permissions=()),
        admin_url(r'^home/$', HomeView.as_view(), name='home', permissions=()),
        admin_url(r'^wizard/$', WizardView.as_view(), name='wizard', permissions=()),
        admin_url(r'^tour/$', TourView.as_view(), name='tour', permissions=()),
        admin_url(r'^search/$', SearchView.as_view(), name='search', permissions=()),
        admin_url(r'^select/$', MultiselectAjaxView.as_view(), name='select', permissions=()),
        admin_url(r'^edit/$', EditObjectView.as_view(), name='edit', permissions=()),
        admin_url(r'^menu/$', MenuView.as_view(), name='menu', permissions=()),
        admin_url(r'^toggle-menu/$', MenuToggleView.as_view(), name='menu_toggle', permissions=()),
        admin_url(
            r'^stop-impersonating-staff/$', stop_impersonating_staff,
            name="stop-impersonating-staff", permissions=()
        ),
        admin_url(
            r'^login/$',
            login,
            kwargs={"template_name": "shuup/admin/auth/login.jinja"},
            name='login',
            require_authentication=False,
            permissions=()
        ),
        admin_url(
            r'^logout/$',
            (auth_views.logout if django.VERSION < (2, 0) else auth_views.LogoutView),
            kwargs={"template_name": "shuup/admin/auth/logout.jinja"},
            name='logout',
            require_authentication=False,
            permissions=()
        ),
        admin_url(
            r'^recover-password/(?P<uidb64>.+)/(?P<token>.+)/$',
            ResetPasswordView,
            name='recover_password',
            require_authentication=False,
            permissions=()
        ),
        admin_url(
            r'^request-password/$',
            RequestPasswordView,
            name='request_password',
            require_authentication=False,
            permissions=()
        ),
        admin_url(
            r'^set-language/$',
            csrf_exempt(set_language),
            name="set-language",
            permissions=()
        ),
    ])

    for u in urls:  # pragma: no cover
        if not isinstance(u, AdminRegexURLPattern):
            warnings.warn("Warning! Admin URL %r is not an `AdminRegexURLPattern`." % u)

    # Add Django javascript catalog url
    urls.append(url(r'^i18n.js$', javascript_catalog_all, name='js-catalog'))

    return tuple(urls)


app_name = "shuup_admin"
urlpatterns = get_urls()
