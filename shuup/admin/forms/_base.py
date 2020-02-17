# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.forms.models import ModelForm
from filer.fields.file import AdminFileWidget

from shuup.admin.forms.widgets import FileDnDUploaderWidget
from shuup.utils.multilanguage_model_form import MultiLanguageModelForm


class ShuupAdminForm(MultiLanguageModelForm):

    def __init__(self, **kwargs):
        super(ShuupAdminForm, self).__init__(**kwargs)
        for field in self.fields:
            if issubclass(self.fields[field].widget.__class__, AdminFileWidget):
                self.fields[field].widget = FileDnDUploaderWidget(
                    upload_path="/default", kind="images", clearable=True)


class ShuupAdminFormNoTranslation(ModelForm):
    def __init__(self, **kwargs):
        super(ShuupAdminFormNoTranslation, self).__init__(**kwargs)
        for field in self.fields:
            if issubclass(self.fields[field].widget.__class__, AdminFileWidget):
                self.fields[field].widget = FileDnDUploaderWidget(
                    upload_path="/default", kind="images", clearable=True)
