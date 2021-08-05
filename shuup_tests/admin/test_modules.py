# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os
import pytest
from django.conf import settings
from django.http import HttpResponseRedirect
from django.test.utils import override_settings
from django.utils.timezone import now
from itertools import chain

from shuup.admin import ShuupAdminAppConfig
from shuup.admin.base import AdminModule
from shuup.admin.dashboard import DashboardContentBlock, get_activity
from shuup.admin.menu import get_menu_entry_categories
from shuup.admin.module_registry import get_module_urls, get_modules, replace_modules
from shuup.admin.utils.permissions import set_permissions_for_group
from shuup.admin.views.dashboard import DashboardView
from shuup.admin.views.search import get_search_results
from shuup.testing.factories import get_default_shop, get_default_staff_user
from shuup.testing.utils import apply_request_middleware
from shuup.utils.excs import Problem
from shuup_tests.admin.fixtures.test_module import ARestrictedTestModule, ATestModule
from shuup_tests.utils import empty_iterable
from shuup_tests.utils.faux_users import AnonymousUser, AuthenticatedUser, StaffUser, SuperUser
from shuup_tests.utils.templates import get_templates_setting_for_specific_directories

TEMPLATES_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), "templates"))


def test_admin_module_base(rf, admin_user):
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    am = AdminModule()
    assert empty_iterable(am.get_urls())
    assert empty_iterable(am.get_menu_entries(request))
    assert empty_iterable(am.get_search_results(request, ""))
    assert empty_iterable(am.get_dashboard_blocks(request))
    assert empty_iterable(am.get_notifications(request))
    assert empty_iterable(am.get_activity(request, now()))


def test_module_loading_and_urls():
    with replace_modules([ATestModule, "shuup_tests.admin.fixtures.test_module:ATestModule"]):
        assert all(u.name.startswith("test") for u in get_module_urls())


def test_modules_in_core_admin_work(rf, admin_user):
    get_default_shop()
    request = rf.get("/")
    apply_request_middleware(request, user=admin_user)
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    with replace_modules(ShuupAdminAppConfig.provides["admin_module"]):
        assert all(get_module_urls())
        assert get_menu_entry_categories(request)


def test_search(rf, admin_user):
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    with replace_modules([ATestModule]):
        assert any(sr.to_json()["text"] == "yes" for sr in get_search_results(request, "yes"))
        assert any(sr.url == "/OK" for sr in get_search_results(request, "spooky"))  # Test aliases
        assert any(sr.target == "_blank" for sr in get_search_results(request, "yes"))


def test_notifications(rf):
    request = rf.get("/")
    with replace_modules([ATestModule]):
        assert any(n.text == "OK" for n in chain(*(m.get_notifications(request) for m in get_modules())))


def test_dashboard_blocks(rf):
    request = rf.get("/")
    with replace_modules([ATestModule]):
        block_ids = set()
        for block in chain(*(m.get_dashboard_blocks(request) for m in get_modules())):
            block_ids.add(block.id)
        assert block_ids >= set(["test-0", "test-1", "test-2", "test-3", "test-4"])


@pytest.mark.django_db
def test_dashboard_blocks_permissions(rf, client):
    with replace_modules([ARestrictedTestModule]):
        request = rf.get("/")
        request.user = get_default_staff_user(get_default_shop())  # Dashboard permission is added by default
        request.session = client.session
        view = DashboardView(request=request)
        assert not view.get_context_data()["blocks"]

        # By default there is only dashboard permission so to be
        # able to see some blocks permission to some admin module
        # providing dashboard bocks needed.
        set_permissions_for_group(
            request.user.groups.first(), set("dashboard") | set(ARestrictedTestModule().get_required_permissions())
        )
        view = DashboardView(request=request)
        assert view.get_context_data()["blocks"]


def test_menu_entries(rf, admin_user):
    request = rf.get("/")
    request.user = admin_user
    with replace_modules([ATestModule]):
        categories = get_menu_entry_categories(request)
        assert categories

        test_category_menu_entries = [cat for cat in categories if cat.name == "Test"][0]
        assert any(me.text == "OK" for me in test_category_menu_entries)


def test_content_block_template(rf):
    TEMPLATES = get_templates_setting_for_specific_directories(settings.TEMPLATES, [TEMPLATES_DIR])
    with override_settings(TEMPLATES=TEMPLATES):
        request = rf.get("/")
        dcb = DashboardContentBlock.by_rendering_template("foo", request, "module_template.jinja", {"name": "world"})
        assert dcb.content == "Hello world"


def test_activity(rf):
    with replace_modules([ATestModule]):
        request = rf.get("/")
        texts = [a.text for a in get_activity(request, 10)]
        # Check that activity is returned in newest-first order.
        assert texts == ["Latest", "Later", "Earlier", "Earliest"]


def test_url_auth(rf):
    def did_disallow(view, request):
        try:
            return isinstance(view(request), HttpResponseRedirect)
        except Problem as prob:
            return True  # Problems are fine here

    with replace_modules([ATestModule]):
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

        request.user = SuperUser()  # Can access all
        assert not did_disallow(urls["test-auth"].callback, request)
        assert not did_disallow(urls["test-perm"].callback, request)
        assert not did_disallow(urls["test-unauth"].callback, request)
