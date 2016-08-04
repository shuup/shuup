# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import django.conf
from django import forms
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from shuup.xtheme import Theme


class ClassicGrayTheme(Theme):
    identifier = "shuup.themes.classic_gray"
    name = "Shuup Classic Gray Theme"
    author = "Shuup Team"
    template_dir = "classic_gray/"

    fields = [
        ("show_welcome_text", forms.BooleanField(required=False, initial=True, label=_("Show Frontpage Welcome Text"))),
    ]

    def get_configuration_form(self, form_kwargs):
        from shuup.xtheme.forms import GenericThemeForm
        return GenericThemeForm(theme=self, **form_kwargs)

    def get_view(self, view_name):
        import shuup.front.themes.views as views
        return getattr(views, view_name, None)

    def _format_cms_links(self, **query_kwargs):
        if "shuup.simple_cms" not in django.conf.settings.INSTALLED_APPS:
            return
        from shuup.simple_cms.models import Page
        for page in Page.objects.visible().filter(**query_kwargs):
            yield {"url": "/%s" % page.url, "text": force_text(page)}

    def get_cms_navigation_links(self):
        return self._format_cms_links(visible_in_menu=True)
