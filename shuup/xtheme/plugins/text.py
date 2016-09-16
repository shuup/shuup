# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import markdown
from django import forms
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from shuup.xtheme.plugins._base import Plugin
from shuup.xtheme.plugins.forms import TranslatableField


class TextPlugin(Plugin):
    """
    Very basic Markdown rendering plugin.
    """
    identifier = "text"
    name = "Text"
    fields = [
        ("text", TranslatableField(
            label=_("text"),
            required=False,
            widget=forms.Textarea,
            attrs={"class": "remarkable-field"}
        ))
    ]

    def render(self, context):  # doccov: ignore
        text = self.get_translated_value("text")
        try:
            markup = markdown.markdown(text)
        except:  # Markdown parsing error? Well, just escape then...
            markup = escape(text)
        return mark_safe(markup)
