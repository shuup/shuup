# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from shuup.admin.modules.settings.forms.system import BaseSettingsForm, BaseSettingsFormPart


class ReportSettingsForm(BaseSettingsForm):
    title = _("Report Settings")
    default_reports_item_limit = forms.IntegerField(
        label=_("Default Report Item Limit"),
        help_text=_("Defines the maximum number of items that will be rendered by a report."),
        required=True,
    )


class ReportSettingsFormPart(BaseSettingsFormPart):
    form = ReportSettingsForm
    name = "report_settings"
    priority = 5
