# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import warnings
from copy import deepcopy

from django import forms
from django.utils.translation import ugettext_lazy as _

from shuup.utils.deprecation import RemovedInFutureShuupWarning
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
            if isinstance(self.theme.stylesheets[0], dict):
                choices = [(style["stylesheet"], style["name"]) for style in self.theme.stylesheets]
            else:
                warnings.warn(
                    "Warning! Using list of tuples in `theme.stylesheets` will deprecate "
                    "in Shuup 0.5.7. Use list of dictionaries instead.", RemovedInFutureShuupWarning)
                choices = self.theme.stylesheets
            self.fields["stylesheet"] = forms.ChoiceField(
                label=_("Stylesheets"), choices=choices, initial=choices[0], required=True, help_text=_(
                    "The fonts, colors, and styles to use with your theme."
                )
            )

        fields = self.theme.fields
        if hasattr(fields, "items"):  # Quacks like a dict; that's fine too
            fields = fields.items()
        for name, field in fields:
            self.fields[name] = deepcopy(field)

        self.initial.update(self.instance.get_settings())

    def save(self, commit=True):
        """
        Save theme settings into the ThemeSettings instance.

        :param commit: Commit flag. Default is True and will raise a ValueError if it is defined in any way.
                        This field is here only to ensure the compatibility with the superclass.
        :type commit: bool
        :return: The now saved `ThemeSettings` instance
        :rtype: shuup.xtheme.models.ThemeSettings
        """
        if not commit:
            raise ValueError(
                "Error! This form does not support `commit=False` or any other value. "
                "This field is here only to ensure the compatibility with the superclass."
            )
        self.instance.update_settings(self.cleaned_data)
        return self.instance
