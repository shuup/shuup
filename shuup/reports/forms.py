# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.forms import ChoiceField, DateTimeField, HiddenInput
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumField

from shuup.core.models import Shop
from shuup.reports.utils import parse_date_range
from shuup.reports.writer import get_writer_names
from shuup.utils.django_compat import force_text


class DateRangeChoices(Enum):
    CUSTOM = "custom"
    TODAY = "today"
    RUNNING_WEEK = "running_week"
    RUNNING_MONTH = "running_month"
    THIS_WEEK = "this_week"
    THIS_MONTH = "this_month"
    THIS_YEAR = "this_year"
    ALL_TIME = "all_time"

    class Labels:
        CUSTOM = _("Custom")
        TODAY = _("Today")
        RUNNING_WEEK = _("Running Week (last 7 days)")
        RUNNING_MONTH = _("Running Month (last 30 days)")
        THIS_WEEK = _("This Week")
        THIS_MONTH = _("This Month")
        THIS_YEAR = _("This Year")
        ALL_TIME = _("All Time")


class ShuupReportForm(forms.Form):
    report = forms.CharField(widget=HiddenInput)
    writer = forms.ChoiceField(
        label=_("Output Format"),
        initial="html",
        choices=[(name, name.title()) for name in sorted(get_writer_names())],
        help_text=_("The format to show the report results."),
    )
    force_download = forms.BooleanField(
        required=False, label=_("Download"), help_text=_("Enable this to download the report.")
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(ShuupReportForm, self).__init__(*args, **kwargs)

    def get_report_instance(self, request=None):
        """
        :rtype: shuup.reports.reporter.base.ShuupReportBase
        """
        from shuup.reports.report import get_report_class

        data = self.cleaned_data

        report_class = get_report_class(data["report"], request)
        writer_name = data.pop("writer")
        if request:
            data.update({"request": request})
        report = report_class(writer_name=writer_name, **data)
        return report


class BaseReportForm(ShuupReportForm):
    shop = forms.ChoiceField(label=_("Shop"), help_text=_("Filter report results by shop."))
    date_range = EnumField(DateRangeChoices).formfield(
        form_class=ChoiceField,
        label=_("Date Range"),
        initial=DateRangeChoices.RUNNING_WEEK,
        help_text=_("Filter report results by a date range."),
    )
    start_date = DateTimeField(label=_("Start Date"), required=False, help_text=_("For a custom date range."))
    end_date = DateTimeField(label=_("End Date"), required=False, help_text=_("For a custom date range."))

    def __init__(self, *args, **kwargs):
        super(BaseReportForm, self).__init__(*args, **kwargs)
        self.fields["shop"].choices = [(shop.pk, shop.name) for shop in Shop.objects.get_for_user(self.request.user)]

    def clean(self):
        data = self.cleaned_data
        if data.get("date_range") == DateRangeChoices.CUSTOM:
            try:
                data["date_range"] = parse_date_range((data["start_date"], data["end_date"]))
            except Exception as exc:
                self.add_error("__all__", force_text(exc))
        return data
