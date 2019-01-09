# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.utils.translation import ugettext_lazy as _


class PrintoutsEmailForm(forms.Form):
    to = forms.EmailField(max_length=256)
    subject = forms.CharField(max_length=256)
    body = forms.CharField(max_length=512, widget=forms.Textarea)

    class Meta:
        labels = {
            "to": _("To"),
            "subject": _("Email Subject"),
            "body": _("Email Body")
        }
