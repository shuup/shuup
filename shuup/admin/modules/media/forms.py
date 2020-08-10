# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms

from shuup.core.models import MediaFolder


class MediaFolderForm(forms.ModelForm):
    class Meta:
        model = MediaFolder
        fields = (
            "user_access", "root_folder_for"
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user_access'].required = False
        self.fields['root_folder_for'].required = False
