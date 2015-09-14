# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django import forms
from django.utils.translation import ugettext_lazy as _

from shoop.apps import AppConfig
from shoop.xtheme.theme import Theme


class ClassicGrayTheme(Theme):
    identifier = "shoop.themes.classic_gray"
    name = "Shoop Classic Gray Theme"
    author = "Juha Kujala"
    template_dir = "classic_gray/"

    fields = [
        ("footer_html", forms.CharField(required=False, label=_("Footer custom HTML"), widget=forms.Textarea)),
        ("footer_links", forms.CharField(required=False, label=_("Footer links"), widget=forms.Textarea,
                                         help_text=_("One line per link in format '[url] [label]'"))),
        ("footer_column_order", forms.ChoiceField(required=False, initial="", label=_("Footer column order"))),
    ]

    def get_configuration_form(self, form_kwargs):
        from .config_form import ClassicGrayConfigForm
        return ClassicGrayConfigForm(theme=self, **form_kwargs)

    def get_view(self, view_name):
        import shoop.themes.classic_gray.views as views
        return getattr(views, view_name, None)


class ClassicGrayThemeAppConfig(AppConfig):
    name = "shoop.themes.classic_gray"
    verbose_name = ClassicGrayTheme.name
    label = "shoop.themes.classic_gray"
    provides = {
        "xtheme": "shoop.themes.classic_gray:ClassicGrayTheme",
        "xtheme_plugin": [
            "shoop.themes.classic_gray.plugins:ProductHighlightPlugin",
        ]
    }


default_app_config = "shoop.themes.classic_gray.ClassicGrayThemeAppConfig"
