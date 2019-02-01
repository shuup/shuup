# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.http.response import HttpResponse, HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView

from shuup import configuration
from shuup.admin.views.wizard import TemplatedWizardFormDef, WizardPane
from shuup.core import telemetry


class TelemetryView(TemplateView):
    template_name = "shuup/admin/system/telemetry.jinja"

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


class TelemetryWizardForm(forms.Form):

    def __init__(self, **kwargs):
        self.shop = kwargs.pop("shop")
        super(TelemetryWizardForm, self).__init__(**kwargs)

        self.fields["opt_in_telemetry"] = forms.BooleanField(
            label=_("Opt-in for telemetry"),
            required=False,
            initial=not telemetry.is_opt_out(),
            widget=forms.CheckboxInput()
        )

    def save(self):
        if not self.is_valid():
            return
        opt_in_telemetry = not self.cleaned_data.get("opt_in_telemetry", False)
        telemetry.set_opt_out(opt_in_telemetry)


class TelemetryWizardPane(WizardPane):
    """
    Wizard Pane to add initial content pages and configure some behaviors of the shop
    """
    identifier = "telemetry"
    icon = "shuup_admin/img/configure.png"
    title = _("Telemetry")  # Shown in home action button
    text = _("Telemetry")  # Shown in wizard view

    def visible(self):
        return True

    def valid(self):
        from shuup.admin.utils.permissions import has_permission
        return has_permission(self.request.user, "xtheme.config")

    def get_form_defs(self):
        form_defs = []

        context = {
            "opt_in": not telemetry.is_opt_out(),
            "is_grace": telemetry.is_in_grace_period(),
            "last_submission_time": telemetry.get_last_submission_time(),
            "submission_data": telemetry.get_telemetry_data(request=self.request, indent=2),
            "title": _("Telemetry")
        }
        form_defs.append(
            TemplatedWizardFormDef(
                name=self.identifier,
                template_name="shuup/admin/system/telemetry_wizard.jinja",
                form_class=TelemetryWizardForm,
                context=context,
                kwargs={"shop": self.object}
            )
        )
        return form_defs

    def form_valid(self, form):
        content_form = form[self.identifier]
        content_form.save()
        configuration.set(None, "wizard_telemetry_completed", True)
