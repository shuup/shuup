# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms


class ColumnSettingsForm(forms.Form):
    settings = None
    non_selected = []
    selected = []

    def __init__(self, settings, *args, **kwargs):
        super(ColumnSettingsForm, self).__init__(*args, **kwargs)
        self.settings = settings
        self.selected = [settings.get_settings_key(c.id) for c in settings.active_columns]
        self.non_selected = [settings.get_settings_key(c.id) for c in settings.inactive_columns]

        for column in settings.column_spec:
            settings_key = settings.get_settings_key(column.id)
            self.fields[settings_key] = forms.BooleanField(label=column.title, required=False)
