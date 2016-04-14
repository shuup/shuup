# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from filer.fields.file import AdminFileWidget

from shoop.admin.forms.widgets import MediaChoiceWidget
from shoop.utils.multilanguage_model_form import MultiLanguageModelForm


class ShoopAdminForm(MultiLanguageModelForm):

    def __init__(self, **kwargs):
        super(ShoopAdminForm, self).__init__(**kwargs)
        for field in self.fields:
            if issubclass(self.fields[field].widget.__class__, AdminFileWidget):
                self.fields[field].widget = MediaChoiceWidget(clearable=True)
