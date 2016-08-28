# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms


class ColumnSettingsForm(forms.Form):
    def __init__(self, settings, *args, **kwargs):
        super(ColumnSettingsForm, self).__init__(*args, **kwargs)
        for col in settings.column_spec:
            self.fields[settings.get_settings_key(col.id)] = forms.BooleanField(label=col.title, required=False)
