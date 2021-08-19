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


class FrontSettingsForm(BaseSettingsForm):
    title = _("Front Settings")
    front_max_upload_size = forms.IntegerField(
        label=_("Front Max Upload Size"),
        help_text=_("Maximum allowed file size (in bytes) for uploads in frontend."),
        required=True,
    )


class FrontSettingsFormPart(BaseSettingsFormPart):
    form = FrontSettingsForm
    name = "front_settings"
    priority = 4
