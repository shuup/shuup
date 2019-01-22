# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.template.loader import render_to_string
from django.utils.encoding import force_text
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


class XThemeSelect2ModelMultipleChoiceField(forms.MultipleChoiceField):
    def __init__(self, model, required=True, label=None,
                 initial=None, help_text='', extra_widget_attrs={}, *args, **kwargs):
        widget_attrs = {"data-model": model}
        widget_attrs.update(extra_widget_attrs)

        choices = []
        if initial:
            from django.apps import apps
            app_label, model_name = model.split(".")
            model = apps.get_model(app_label, model_name)
            choices = [
                (instance.pk, force_text(instance))
                for instance in model.objects.filter(pk__in=initial)
            ]

        super(XThemeSelect2ModelMultipleChoiceField, self).__init__(
            choices=choices,
            required=required,
            widget=forms.SelectMultiple(attrs=widget_attrs),
            label=label,
            initial=initial,
            help_text=help_text,
            *args, **kwargs
        )

    def validate(self, value):
        if self.required and not value:
            raise forms.ValidationError(self.error_messages['required'], code='required')


class XThemeSelect2ModelChoiceField(forms.ChoiceField):
    def __init__(self, model, required=True, label=None,
                 initial=None, help_text='', extra_widget_attrs={}, *args, **kwargs):
        widget_attrs = {"data-model": model}
        widget_attrs.update(extra_widget_attrs)

        choices = []
        if initial:
            from django.apps import apps
            app_label, model_name = model.split(".")
            model = apps.get_model(app_label, model_name)
            instance = model.objects.filter(pk=initial).first()
            if instance:
                choices = [(instance.pk, force_text(instance))]

        super(XThemeSelect2ModelChoiceField, self).__init__(
            choices=choices,
            required=required,
            widget=forms.Select(attrs=widget_attrs),
            label=label,
            initial=initial,
            help_text=help_text,
            *args, **kwargs
        )

    def validate(self, value):
        if self.required and not value:
            raise forms.ValidationError(self.error_messages['required'], code='required')
