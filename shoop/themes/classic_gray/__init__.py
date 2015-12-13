# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import django.conf
from django import forms
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from shoop.apps import AppConfig
from shoop.xtheme import Theme


class ClassicGrayTheme(Theme):
    identifier = "shoop.themes.classic_gray"
    name = "Shoop Classic Gray Theme"
    author = "Juha Kujala"
    template_dir = "classic_gray/"

    fields = [
        ("show_welcome_text", forms.BooleanField(required=False, initial=True, label=_("Show Frontpage Welcome Text"))),
        ("footer_html", forms.CharField(required=False, label=_("Footer custom HTML"), widget=forms.Textarea)),
        ("footer_links", forms.CharField(required=False, label=_("Footer links"), widget=forms.Textarea,
                                         help_text=_("One line per link in format 'http://example.com Example Link'"))),
        ("footer_column_order", forms.ChoiceField(required=False, initial="", label=_("Footer column order"))),
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
            url = line[0]
            if "//" not in url and not url.startswith("/"):  # "Fix up" relative URLs and CMS page identifiers
                url = "/%s" % url
            if len(line) == 2:
                yield {"url": url, "text": line[1]}
            else:
                yield {"url": url}

    def _format_cms_links(self, **query_kwargs):
        if "shoop.simple_cms" not in django.conf.settings.INSTALLED_APPS:
            return
        from shoop.simple_cms.models import Page
        for page in Page.objects.visible().filter(**query_kwargs):
            yield {"url": "/%s" % page.url, "text": force_text(page)}

    def get_cms_navigation_links(self):
        return self._format_cms_links(visible_in_menu=True)

    def get_cms_footer_links(self):
        page_ids = self.get_setting("footer_cms_pages") or []
        return self._format_cms_links(id__in=page_ids)


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
