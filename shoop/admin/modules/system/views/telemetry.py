# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django.http.response import HttpResponse, HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView

from shoop.core import telemetry


class TelemetryView(TemplateView):
    template_name = "shoop/admin/system/telemetry.jinja"

    def get_context_data(self, **kwargs):
        context = super(TelemetryView, self).get_context_data(**kwargs)
        context.update({
            "opt_in": not telemetry.is_opt_out(),
            "is_grace": telemetry.is_in_grace_period(),
            "last_submission_time": telemetry.get_last_submission_time(),
            "submission_data": telemetry.get_telemetry_data(request=self.request, indent=2),
            "title": _("Telemetry")
        })
        return context

    def get(self, request, *args, **kwargs):
        if "last" in request.GET:
            return HttpResponse(telemetry.get_last_submission_data(), content_type="text/plain; charset=UTF-8")
        return super(TelemetryView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        opt = request.POST.get("opt")
        if opt:
            telemetry.set_opt_out(opt == "out")
        return HttpResponseRedirect(request.path)
