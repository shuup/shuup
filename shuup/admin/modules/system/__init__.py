# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry, Notification
from shuup.admin.menu import SETTINGS_MENU_CATEGORY
from shuup.admin.utils.urls import admin_url
from shuup.core.telemetry import is_in_grace_period, is_opt_out, is_telemetry_enabled


class SystemModule(AdminModule):
    name = _("System")

    def get_urls(self):
        return [
            admin_url(
                "^system/telemetry/$", "shuup.admin.modules.system.views.telemetry.TelemetryView", name="telemetry"
            )
        ]

    def get_menu_entries(self, request):
        return [
            e
            for e in [
                MenuEntry(
                    text=_("Telemetry"),
                    icon="fa fa-tachometer",
                    url="shuup_admin:telemetry",
                    category=SETTINGS_MENU_CATEGORY,
                )
                if is_telemetry_enabled()
                else None,
            ]
            if e
        ]

    def get_notifications(self, request):
        if is_telemetry_enabled() and is_in_grace_period() and not is_opt_out():
            yield Notification(
                _("Statistics will be periodically sent to Shuup.com after 24 hours. Click here for more information."),
                title=_("Telemetry"),
                kind="info",
                url="shuup_admin:telemetry",
            )
