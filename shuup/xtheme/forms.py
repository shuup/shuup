# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from copy import deepcopy

from django import forms
from django.utils.translation import ugettext_lazy as _

from shuup.xtheme.models import ThemeSettings


class GenericThemeForm(forms.ModelForm):
    """
    A generic form for Xthemes; populates itself based on `fields` in the theme class.
    """

    class Meta:
        model = ThemeSettings
        fields = ()  # Nothing -- we'll populate this ourselves, thank you very much

    def __init__(self, **kwargs):
        self.theme = kwargs.pop("theme")
        super(GenericThemeForm, self).__init__(**kwargs)
        if self.theme.stylesheets:
            self.fields["stylesheet"] = forms.ChoiceField(
                label=_("Stylesheets"), choices=self.theme.stylesheets,
                initial=self.theme.stylesheets[0], required=True)

        fields = self.theme.fields
        if hasattr(fields, "items"):  # Quacks like a dict; that's fine too
            fields = fields.items()
        for name, field in fields:
            self.fields[name] = deepcopy(field)
        self.initial.update(self.instance.get_settings())

    def save(self, commit=True):
        """
        Save theme settings into the ThemeSettings instance

        :param commit: Commit flag. Ignored, but there for compatibility with the superclass.
        :type commit: bool
        :return: The now saved `ThemeSettings` instance
        :rtype: shuup.xtheme.models.ThemeSettings
        """
        if not commit:
            raise ValueError("This form does not support commit=False")
        self.instance.update_settings(self.cleaned_data)
        return self.instance
