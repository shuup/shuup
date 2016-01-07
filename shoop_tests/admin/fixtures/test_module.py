# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import datetime

from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View

from shoop.admin.base import (
    Activity, AdminModule, MenuEntry, Notification, SearchResult
)
from shoop.admin.dashboard import (
    DashboardContentBlock, DashboardMoneyBlock, DashboardNumberBlock,
    DashboardValueBlock
)
from shoop.admin.utils.urls import admin_url


class TestAction(View):
    def dispatch(self, request, *args, **kwargs):
        return HttpResponse("OK")

class TestModule(AdminModule):
    name = _("Test")

    def get_urls(self):
        return [
            admin_url("test/$", TestAction, name="test-auth", require_authentication=True),
            admin_url("test2/$", "shoop_tests.admin.fixtures.test_module.TestAction", name="test-unauth", require_authentication=False),
            admin_url("test3/$", "shoop_tests.admin.fixtures.test_module.TestAction", name="test-perm", require_authentication=True, permissions=("bogus-permission",)),
        ]

    def get_menu_entries(self, request):
        return [MenuEntry(text="OK", url="/OK", category="Test", aliases=("spooky",))]

    def get_search_results(self, request, query):
        return [SearchResult(text=query, url="/OK")]

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
