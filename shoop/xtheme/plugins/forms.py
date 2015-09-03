# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from copy import deepcopy
from django import forms


class PluginForm(forms.Form):
    def __init__(self, **kwargs):
        self.plugin = kwargs.pop("plugin")
        super(PluginForm, self).__init__(**kwargs)
        self.populate()

    def populate(self):  # pragma: no cover
        # Subclass hook (overriding __init__ all the time is such a bore)
        pass

    def get_config(self):
        """
        Get the new `config` dict for a plugin.

        Called when the form is valid, akin to `.save()` for ModelForms.

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
    A generic form for Xtheme plugins; populates itself based on `fields`
    in the plugin class.
    """

    def populate(self):
        fields = self.plugin.fields
        if hasattr(fields, "items"):  # Quacks like a dict; that's fine too
            fields = fields.items()
        for name, field in fields:
            self.fields[name] = deepcopy(field)
        self.initial.update(self.plugin.config)
