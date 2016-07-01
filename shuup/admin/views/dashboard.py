# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.views.generic.base import TemplateView

import shuup
from shuup.admin.dashboard import get_activity
from shuup.admin.module_registry import get_modules
from shuup.admin.utils.permissions import get_missing_permissions
from shuup.core.telemetry import try_send_telemetry


class DashboardView(TemplateView):
    template_name = "shuup/admin/dashboard/dashboard.jinja"

    def get_context_data(self, **kwargs):
        context = super(DashboardView, self).get_context_data(**kwargs)
        context["version"] = shuup.__version__
        context["notifications"] = notifications = []
        context["blocks"] = blocks = []
        for module in get_modules():
            if not get_missing_permissions(self.request.user, module.get_required_permissions()):
                notifications.extend(module.get_notifications(request=self.request))
                blocks.extend(module.get_dashboard_blocks(request=self.request))
        context["activity"] = get_activity(request=self.request)
        return context

    def get(self, request, *args, **kwargs):
        try_send_telemetry(request)
        return super(DashboardView, self).get(request, *args, **kwargs)
