# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shoop.admin.base import AdminModule, MenuEntry, Notification
from shoop.admin.utils.urls import admin_url
from shoop.core.telemetry import is_in_grace_period, is_opt_out, is_telemetry_enabled


class SystemModule(AdminModule):
    name = _("System")
    category = name

    def get_urls(self):
        return [
            admin_url(
                "^system/telemetry/$",
                "shoop.admin.modules.system.views.telemetry.TelemetryView",
                name="telemetry"
            ),
        ]

    def get_menu_category_icons(self):
        return {self.category: "fa fa-wrench"}

    def get_menu_entries(self, request):
        return [e for e in [
            MenuEntry(
                text=_("Telemetry"), icon="fa fa-tachometer", url="shoop_admin:telemetry",
                category=self.category
            ) if is_telemetry_enabled() else None,
        ] if e]

    def get_notifications(self, request):
        if is_telemetry_enabled() and is_in_grace_period() and not is_opt_out():
            yield Notification(
                _("Statistics will be periodically sent to Shoop.io after 24 hours. Click here for more information."),
                title=_("Telemetry"),
                kind="info",
                url="shoop_admin:telemetry"
            )
