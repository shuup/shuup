# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import MediaFolder


class MediaFolderForm(forms.ModelForm):
    class Meta:
        model = MediaFolder
        fields = (
            "visible", "owners"
        )
        labels = {
            "visible": _("Visible for all everyone in the media browser")
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['owners'].required = False
