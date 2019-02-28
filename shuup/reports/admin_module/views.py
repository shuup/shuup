# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView

from shuup.reports.report import get_report_classes
from shuup.reports.writer import get_writer_instance


class ReportView(FormView):
    template_name = "shuup/reports/report.jinja"
    form_class = None
    add_form_errors_as_messages = True

    def get_form(self, form_class=None):
        self.report_classes = get_report_classes(self.request)
        selected_report = self.request.GET.get("report")
        if selected_report:
            return self._get_concrete_form(selected_report)
        return self._get_type_choice_form()

    def _get_concrete_form(self, selected_report):
        form_info = self.report_classes[selected_report]
        self.form_class = form_info.form_class
        return self._get_form(form_info)

    def _get_type_choice_form(self):
        selected_report = self.request.GET.get("report")
        form_info = self.report_classes[selected_report] if selected_report else None
        if not form_info:
            report_classes = get_report_classes(self.request)
            if not report_classes:
                return None
            form_info = six.next(six.itervalues(report_classes))
        self.form_class = form_info.form_class
        return self._get_form(form_info)

    def _get_choices(self):
        return [(k, v.title) for k, v in six.iteritems(get_report_classes(self.request))]

    def _get_form(self, selected):
        form = self.form_class(request=self.request, **self.get_form_kwargs())
        report_field = forms.ChoiceField(
            choices=self._get_choices(),
            label=_("Type"),
            required=True,
            initial=selected.identifier,
            help_text=_("Select the type of report to run.")
        )
        form.fields["report"] = report_field
        return form

    def form_valid(self, form):
        writer = get_writer_instance(form.cleaned_data["writer"])
        report = form.get_report_instance(self.request)
        if not self.request.POST.get("force_download") and writer.writer_type in ("html", "pprint", "json"):
            output = writer.render_report(report, inline=True)
            return self.render_to_response(self.get_context_data(form=form, result=output))
        return writer.get_response(report=report)

    def get_context_data(self, **kwargs):
        context = super(ReportView, self).get_context_data(**kwargs)
        selected_report = self.request.GET.get("report")
        context["current_report"] = self.report_classes[selected_report] if selected_report else None
        return context
