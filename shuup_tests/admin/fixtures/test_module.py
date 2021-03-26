# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import datetime
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View

from shuup.admin.base import Activity, AdminModule, MenuEntry, Notification, SearchResult
from shuup.admin.dashboard import DashboardContentBlock, DashboardMoneyBlock, DashboardNumberBlock, DashboardValueBlock
from shuup.admin.utils.urls import admin_url


class OkAction(View):
    def dispatch(self, request, *args, **kwargs):
        return HttpResponse("OK")


class ATestModule(AdminModule):
    name = _("Test")

    def get_urls(self):
        return [
            admin_url("test/$", OkAction, name="test-auth", require_authentication=True, permissions=()),
            admin_url(
                "test2/$",
                "shuup_tests.admin.fixtures.test_module.OkAction",
                name="test-unauth",
                require_authentication=False,
                permissions=(),
            ),
            admin_url(
                "test3/$",
                "shuup_tests.admin.fixtures.test_module.OkAction",
                name="test-perm",
                require_authentication=True,
                permissions=("bogus-permission",),
            ),
        ]

    def get_menu_entries(self, request):
        return [MenuEntry(text="OK", url="/OK", category="Test", aliases=("spooky",))]

    def get_search_results(self, request, query):
        return [SearchResult(text=query, url="/OK", target="_blank")]

    def get_notifications(self, request):
        return [Notification(text="OK")]

    def get_dashboard_blocks(self, request):
        return [
            DashboardContentBlock(id="test-0", content="Hello", size="invalid"),
            DashboardValueBlock(id="test-1", value="yes", title="hi"),
            DashboardNumberBlock(id="test-2", value=35, title="hello"),
            DashboardNumberBlock(id="test-3", value=35.3, title="hello"),
            DashboardMoneyBlock(id="test-4", value=35, title="hola", currency="USD"),
        ]

    def get_activity(self, request, cutoff):
        t = cutoff + datetime.timedelta(minutes=10)
        yield Activity(datetime=t, text="Earliest")
        yield Activity(datetime=t + datetime.timedelta(minutes=3), text="Earlier")
        yield Activity(datetime=t + datetime.timedelta(minutes=10), text="Latest")
        yield Activity(datetime=t + datetime.timedelta(minutes=5), text="Later")


class ARestrictedTestModule(ATestModule):
    name = _("RestrictedTest")

    def get_menu_entries(self, request):
        return [MenuEntry(text="OK", url="/OK", category="RestrictedTest", aliases=("spooky",))]
