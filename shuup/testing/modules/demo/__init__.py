# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import random

from babel.dates import format_date
from django.http.response import HttpResponse
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import (
    Activity, AdminModule, MenuEntry, Notification, SearchResult
)
from shuup.admin.dashboard import (
    DashboardMoneyBlock, DashboardNumberBlock, DashboardValueBlock
)
from shuup.admin.utils.urls import admin_url
from shuup.testing.text_data import random_title
from shuup.utils.i18n import get_current_babel_locale


class DemoModule(AdminModule):
    name = _("Demo")

    def get_urls(self):
        return [
            admin_url("test/$", lambda request: HttpResponse("herrrp %s" % request)),
        ]

    def check_demo_optin(self, request):
        """
        Check whether or not the user has opted in to see demo content.
        This may be toggled with ?demo=0 or ?demo=1, and it's a persistent
        session flag.

        :param request: HTTP request
        :type request: django.http.HttpRequest
        :return: Opt-in flag
        :rtype: bool
        """
        demo = request.GET.get("demo")
        if demo is not None:
            request.session["demo"] = bool(int(demo))
        return bool(request.session.get("demo"))

    def get_menu_entries(self, request):
        if not self.check_demo_optin(request):
            return
        return [
            MenuEntry(
                text=random_title(),
                icon="fa %s" % random.choice(["fa-flash", "fa-folder", "fa-eye", "fa-dollar", "fa-paw", "fa-cloud"]),
                url="https://google.com/",
                category="Test %d" % random.randint(1, 6)
            ) for x in range(30)
        ]

    def get_search_results(self, request, query):
        if not self.check_demo_optin(request):
            return
        for word in query.split():
            if word:
                yield SearchResult(word, url="https://google.com/?q=%s" % word)
                yield SearchResult(word[::-1], url="https://google.com/?q=%s" % word[::-1])
        yield SearchResult("Create test: %s" % query, url="http://about:blank", icon="fa fa-plus", is_action=True)

    def get_notifications(self, request):
        if not self.check_demo_optin(request):
            return
        yield Notification(text="Your IP is %s" % request.META.get("REMOTE_ADDR"))
        yield Notification(title="Dice", text="Your lucky number is %d" % random.randint(1, 43), kind="success")
        yield Notification(title="Stock Alert", text="Items X, Y, Z are running low", kind="warning")
        yield Notification(title="Outstanding Orders", text="10 orders have not been touched in 7 days", kind="danger")

    def get_dashboard_blocks(self, request):
        if not self.check_demo_optin(request):
            return
        locale = get_current_babel_locale()
        n = now()
        weekday = format_date(n, "EEEE", locale=locale)
        today = format_date(n, locale=locale)
        yield DashboardValueBlock(
            id="test-x", color="blue", title="Happy %s!" % weekday, value=today, icon="fa fa-calendar"
        )
        yield DashboardNumberBlock(
            id="test-x", color="red", title="Visitors Yesterday", value=random.randint(2200, 10000), icon="fa fa-globe"
        )
        yield DashboardNumberBlock(id="test-x", color="gray", title="Registered Users", value=1240, icon="fa fa-user")
        yield DashboardNumberBlock(id="test-x", color="orange", title="Orders", value=32, icon="fa fa-inbox")
        yield DashboardMoneyBlock(
            id="test-x", color="green", title="Open Orders Value", value=32000, currency="USD", icon="fa fa-line-chart"
        )
        yield DashboardNumberBlock(id="test-x", color="yellow", title="Current Visitors", value=6, icon="fa fa-users")
        yield DashboardMoneyBlock(
            id="test-x", color="none", title="Sales this week", value=430.30, currency="USD", icon="fa fa-dollar"
        )
        yield DashboardValueBlock(
            id="test-1", value="\u03C0", title="The most delicious number", color="purple", icon="fa fa-smile-o"
        )

    def get_activity(self, request, cutoff):
        if not self.check_demo_optin(request):
            return
        t = now().replace(minute=0, second=0)
        yield Activity(t, "It was %s" % t)
