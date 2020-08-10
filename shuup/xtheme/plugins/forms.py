# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from collections import OrderedDict
from copy import deepcopy

import six
from django import forms
from django.conf import settings

from shuup.xtheme.plugins.consts import FALLBACK_LANGUAGE_CODE


class PluginForm(forms.Form):
    """
    Base class for plugin configuration forms.
    """

    def __init__(self, **kwargs):
        self.plugin = kwargs.pop("plugin")
        self.request = kwargs.pop("request")
        super(PluginForm, self).__init__(**kwargs)
        self.populate()
        self.set_defaults()
        self.init_translated_fields()

    def populate(self):  # pragma: no cover, doccov: ignore
        # Subclass hook (overriding __init__ all the time is such a bore)
        pass

    def init_translated_fields(self):
        self.translatable_field_names = []
        self.monolingual_field_names = []
        languages = self.get_languages()
        new_fields = OrderedDict()
        for name, field in six.iteritems(self.fields):
            if isinstance(field, TranslatableField):
                self.translatable_field_names.append(name)
                for language_code in languages:
                    key = "%s_%s" % (name, language_code)
                    new_fields[key] = deepcopy(field)
                    new_fields[key].initial = self.plugin.get_translated_value(name, language=language_code)
                    new_fields[key].required = False
            elif field:
                self.monolingual_field_names.append(name)
                new_fields[name] = field
        self.fields = new_fields

    def set_defaults(self):
        """
        Set the forms initial values based on plugin defaults

        Use the plugin's default configuration as the default form field
        initial values.
        """
        for key, value in self.plugin.get_defaults().items():
            if key in self.fields and self.fields[key].initial is None:
                self.fields[key].initial = value

    def full_clean(self):
        """
        Use initial values as defaults for cleaned data
        """
        super(PluginForm, self).full_clean()
        for name in self.fields:
            if name in self.cleaned_data:
                continue
            if self.fields[name].initial is not None:
                self.cleaned_data[name] = self.fields[name].initial
        self.cleaned_data

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
        data = self.cleaned_data.copy()
        languages = self.get_languages()
        for field_name in self.translatable_field_names:
            data[field_name] = {}
            for language_code in languages:
                key = "%s_%s" % (field_name, language_code)
                val = self.cleaned_data.get(key, "")
                if val not in ["", None]:
                    data[field_name][language_code] = val
                del data[key]
        config.update(data)
        return config

    def get_languages(self):
        default_language = settings.PARLER_DEFAULT_LANGUAGE_CODE
        languages = [language[0] for language in settings.LANGUAGES]

        if default_language in languages:
            languages.remove(default_language)

        return [default_language] + languages + [FALLBACK_LANGUAGE_CODE]


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
    pass  # used solely to flag fields as translatable
