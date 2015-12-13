# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from copy import deepcopy

from django import forms
from django.conf import settings

from shoop.xtheme.plugins.widgets import TranslatableFieldWidget


class PluginForm(forms.Form):
    """
    Base class for plugin configuration forms.
    """

    def __init__(self, **kwargs):
        self.plugin = kwargs.pop("plugin")
        super(PluginForm, self).__init__(**kwargs)
        self.populate()

    def populate(self):  # pragma: no cover, doccov: ignore
        # Subclass hook (overriding __init__ all the time is such a bore)
        pass

    def get_config(self):
        """
        Get the new `config` dict for a plugin.

        Called when the form is valid, akin to
        `django.forms.models.ModelForm.save`.

        The default implementation just augments the old config with the
        cleaned data for the form.

        :return: A new JSONable (!) config dict
        :rtype: dict
        """

        config = self.plugin.config.copy()
        config.update(self.cleaned_data)
        return config


class GenericPluginForm(PluginForm):
    """
    A generic form for Xtheme plugins; populates itself based on `fields` in the plugin class.
    """

    def populate(self):  # doccov: ignore
        fields = self.plugin.fields
        if hasattr(fields, "items"):  # Quacks like a dict; that's fine too
            fields = fields.items()
        for name, field in fields:
            self.fields[name] = deepcopy(field)
        self.initial.update(self.plugin.config)


class TranslatableField(forms.Field):
    widget = TranslatableFieldWidget

    def __init__(self, *args, **kwargs):
        input_widget = kwargs.pop("widget", forms.TextInput)  # Only allow overriding the subwidget.
        languages = kwargs.pop("languages", [l[0] for l in settings.LANGUAGES])  # TODO: Another language source?
        kwargs["widget"] = self.widget(languages=languages, input_widget=input_widget)
        super(TranslatableField, self).__init__(*args, **kwargs)

    def clean(self, value):
        assert isinstance(value, dict)
        return value
