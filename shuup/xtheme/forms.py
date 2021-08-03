# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import warnings
from copy import deepcopy
from django import forms
from django.forms.widgets import TextInput
from django.urls.base import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from shuup.admin.forms.fields import ObjectSelect2ModelField
from shuup.admin.forms.quick_select import QuickAddRelatedObjectSelect
from shuup.admin.forms.widgets import FileDnDUploaderWidget
from shuup.admin.shop_provider import get_shop
from shuup.utils.deprecation import RemovedInFutureShuupWarning
from shuup.xtheme.models import Font, ThemeSettings

from .models import AdminThemeSettings


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
                    "in Shuup 0.5.7. Use list of dictionaries instead.",
                    RemovedInFutureShuupWarning,
                )
                choices = self.theme.stylesheets
            self.fields["stylesheet"] = forms.ChoiceField(
                label=_("Stylesheets"),
                choices=choices,
                initial=choices[0],
                required=True,
                help_text=_("The fonts, colors, and styles to use with your theme."),
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


class FontForm(forms.ModelForm):
    class Meta:
        model = Font
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(FontForm, self).__init__(*args, **kwargs)
        self.fields["woff"].widget = FileDnDUploaderWidget(upload_path="/admin_typography/", clearable=True)
        self.fields["woff2"].widget = FileDnDUploaderWidget(upload_path="/admin_typography/", clearable=True)
        self.fields["ttf"].widget = FileDnDUploaderWidget(upload_path="/admin_typography/", clearable=True)
        self.fields["svg"].widget = FileDnDUploaderWidget(upload_path="/admin_typography/", clearable=True)
        self.fields["eot"].widget = FileDnDUploaderWidget(upload_path="/admin_typography/", clearable=True)

    def save(self, commit=True):
        self.instance.shop = get_shop(self.request)
        return super(FontForm, self).save(commit)


class QuickAddFontSelect(QuickAddRelatedObjectSelect):
    url = reverse_lazy("shuup_admin:xtheme.font.new")
    model = "xtheme.Font"


class AdminThemeForm(forms.ModelForm):
    class Meta:
        model = AdminThemeSettings
        fields = "__all__"
        labels = {
            "primary_color": _("Choose the primary color:"),
            "secondary_color": _("Choose the secondary color:"),
            "text_color": _("Choose the primary text color:"),
            "success_color": _("Choose the success (green) style primary color:"),
            "danger_color": _("Choose the danger (red) style primary color:"),
        }
        widgets = {
            "primary_color": TextInput(attrs={"type": "color"}),
            "secondary_color": TextInput(attrs={"type": "color"}),
            "text_color": TextInput(attrs={"type": "color"}),
            "success_color": TextInput(attrs={"type": "color"}),
            "danger_color": TextInput(attrs={"type": "color"}),
        }

    def __init__(self, *args, **kwargs):
        super(AdminThemeForm, self).__init__(*args, **kwargs)

        if self.instance.pk:
            initial_header_font = self.instance.admin_header_font
            initial_body_font = self.instance.admin_body_font
        else:
            initial_header_font = kwargs.get("initial", {}).get("admin_header_font")
            initial_body_font = kwargs.get("initial", {}).get("admin_body_font")

        self.fields["admin_header_font"] = ObjectSelect2ModelField(
            label=_("Admin Header Font"),
            initial=initial_header_font,
            model=Font,
            required=False,
            widget=QuickAddFontSelect(editable_model=Font, initial=initial_header_font),
        )
        self.fields["admin_body_font"] = ObjectSelect2ModelField(
            label=_("Admin Body Font"),
            initial=initial_body_font,
            model=Font,
            required=False,
            widget=QuickAddFontSelect(editable_model=Font, initial=initial_body_font),
        )
