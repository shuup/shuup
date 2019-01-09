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
