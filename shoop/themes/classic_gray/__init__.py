# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django import forms
from django.conf import settings
from django.utils.encoding import force_text
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
        ("show_welcome_text", forms.BooleanField(required=False, initial=True, label=_("Show Frontpage Welcome Text"))),
    ]

    def get_configuration_form(self, form_kwargs):
        from .config_form import ClassicGrayConfigForm
        return ClassicGrayConfigForm(theme=self, **form_kwargs)

    def get_view(self, view_name):
        import shoop.themes.classic_gray.views as views
        return getattr(views, view_name, None)

    def get_footer_links(self):
        for line in (self.get_setting("footer_links") or "").splitlines():
            line = line.strip()
            if not line:
                continue
            line = line.split(None, 1)
            if len(line) == 2:
                yield {"url": line[0], "text": line[1]}
            else:
                yield {"url": line[0]}

    def get_cms_links(self):
        if "shoop.simple_cms" not in settings.INSTALLED_APPS:
            return
        from shoop.simple_cms.models import Page
        for page in Page.objects.visible().filter(visible_in_menu=True):
            yield {"url": page.url, "text": force_text(page)}


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
