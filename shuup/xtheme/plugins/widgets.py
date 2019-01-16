# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe


class XThemeModelChoiceWidget(forms.Select):
    def render(self, name, value, attrs=None, choices=()):
        return mark_safe(
            render_to_string("shuup/xtheme/_model_widget.jinja", {
                "name": name,
                "selected_value": value,
                "objects": self.choices,
            })
        )


class XThemeModelChoiceField(forms.ModelChoiceField):
    widget = XThemeModelChoiceWidget

    def label_from_instance(self, obj):
        return obj


class XThemeMultipleChoiceField(forms.MultipleChoiceField):
    """
    A custom option field that doesn't validate whether the selected value
    is in choices field as that is created dynamically
    """
    def __init__(self, choices=(), required=True, widget=None, label=None,
                 initial=None, help_text='', validate_choices=True, *args, **kwargs):
        self.validate_choices = validate_choices
        super(XThemeMultipleChoiceField, self).__init__(
            choices=choices, required=required, widget=widget, label=label,
            initial=initial, help_text=help_text, *args, **kwargs
        )

    def validate(self, value):
        if self.validate_choices:
            super(XThemeMultipleChoiceField, self).validate(value)
        else:
            if self.required and not value:
                raise forms.ValidationError(self.error_messages['required'], code='required')
