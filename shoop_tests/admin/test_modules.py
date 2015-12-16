# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import os
from copy import deepcopy
from itertools import chain

from django.conf import settings
from django.http import HttpResponseRedirect
from django.test.utils import override_settings
from django.utils.timezone import now

from shoop.admin import ShoopAdminAppConfig
from shoop.admin.base import AdminModule
from shoop.admin.dashboard import DashboardContentBlock, get_activity
from shoop.admin.menu import get_menu_entry_categories
from shoop.admin.module_registry import (
    get_module_urls, get_modules, replace_modules
)
from shoop.admin.views.search import get_search_results
from shoop.testing.factories import get_default_shop
from shoop.testing.utils import apply_request_middleware
from shoop.utils.excs import Problem
from shoop_tests.admin.fixtures.test_module import TestModule
from shoop_tests.utils import empty_iterable
from shoop_tests.utils.faux_users import (
    AnonymousUser, AuthenticatedUser, StaffUser, SuperUser
)
from shoop_tests.utils.templates import \
    get_templates_setting_for_specific_directories

TEMPLATES_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), "templates"))


def test_admin_module_base(rf):
    request = rf.get("/")
    am = AdminModule()
    assert empty_iterable(am.get_urls())
    assert empty_iterable(am.get_menu_entries(request))
    assert empty_iterable(am.get_search_results(request, ""))
    assert empty_iterable(am.get_dashboard_blocks(request))
    assert empty_iterable(am.get_notifications(request))
    assert empty_iterable(am.get_activity(request, now()))


def test_module_loading_and_urls():
    with replace_modules([
        TestModule,
        "shoop_tests.admin.fixtures.test_module:TestModule"
    ]):
        assert all(u.name.startswith("test") for u in get_module_urls())


def test_modules_in_core_admin_work(rf, admin_user):
    get_default_shop()
    request = rf.get("/")
    apply_request_middleware(request, user=admin_user)
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    with replace_modules(ShoopAdminAppConfig.provides["admin_module"]):
        assert all(get_module_urls())
        assert get_menu_entry_categories(request)


def test_search(rf):
    request = rf.get("/")
    with replace_modules([TestModule]):
        assert any(sr.to_json()["text"] == "yes" for sr in get_search_results(request, "yes"))
        assert any(sr.url == "/OK" for sr in get_search_results(request, "spooky"))  # Test aliases


def test_notifications(rf):
    request = rf.get("/")
    with replace_modules([TestModule]):
        assert any(n.text == "OK" for n in chain(*(m.get_notifications(request) for m in get_modules())))


def test_dashboard_blocks(rf):
    request = rf.get("/")
    with replace_modules([TestModule]):
        block_ids = set()
        for block in chain(*(m.get_dashboard_blocks(request) for m in get_modules())):
            block_ids.add(block.id)
        assert block_ids >= set(["test-0", "test-1", "test-2", "test-3", "test-4"])


def test_menu_entries(rf):
    request = rf.get("/")
    with replace_modules([TestModule]):
        test_category_menu_entries = get_menu_entry_categories(request).get("Test")
        assert any(me.text == "OK" for me in test_category_menu_entries)


def test_content_block_template(rf):
    TEMPLATES = get_templates_setting_for_specific_directories(settings.TEMPLATES, [TEMPLATES_DIR])
    with override_settings(TEMPLATES=TEMPLATES):
        request = rf.get("/")
        dcb = DashboardContentBlock.by_rendering_template("foo", request, "module_template.jinja", {
            "name": "world"
        })
        assert dcb.content == "Hello world"


def test_activity(rf):
    with replace_modules([TestModule]):
        request = rf.get("/")
        texts = [a.text for a in get_activity(request, 10)]
        # Check that activity is returned in newest-first order.
        assert texts == ["Latest", "Later", "Earlier", "Earliest" ]


def test_url_auth(rf):
    def did_disallow(view, request):
        try:
            return isinstance(view(request), HttpResponseRedirect)
        except Problem as prob:
            return True  # Problems are fine here

    with replace_modules([TestModule]):
        urls = dict((u.name, u) for u in get_module_urls())
        request = rf.get("/")

        request.user = AnonymousUser()
        assert did_disallow(urls["test-auth"].callback, request)
        assert did_disallow(urls["test-perm"].callback, request)
        assert not did_disallow(urls["test-unauth"].callback, request)
        request.user = AuthenticatedUser()
        assert did_disallow(urls["test-auth"].callback, request)
        assert did_disallow(urls["test-perm"].callback, request)
        assert not did_disallow(urls["test-unauth"].callback, request)
        request.user = StaffUser()
        assert not did_disallow(urls["test-auth"].callback, request)
        assert did_disallow(urls["test-perm"].callback, request)
        assert not did_disallow(urls["test-unauth"].callback, request)
        request.user = SuperUser()
        assert not did_disallow(urls["test-auth"].callback, request)
        assert not did_disallow(urls["test-perm"].callback, request)
        assert not did_disallow(urls["test-unauth"].callback, request)
