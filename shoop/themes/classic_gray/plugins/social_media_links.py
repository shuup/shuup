# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.utils.translation import ugettext_lazy as _

from shoop.social_media.models import SocialMediaLink
from shoop.xtheme import TemplatedPlugin
from shoop.xtheme.plugins.forms import GenericPluginForm, TranslatableField


class SocialMediaLinksPluginForm(GenericPluginForm):
    def clean(self):
        cleaned_data = super(SocialMediaLinksPluginForm, self).clean()
        links = cleaned_data.get("links")
        cleaned_data["links"] = [link.pk for link in links]
        return cleaned_data


class SocialMediaLinksPlugin(TemplatedPlugin):
    identifier = "classic_gray.social_media_links"
    name = _("Social Media Links")
    template_name = "classic_gray/plugins/social_media_links.jinja"
    editor_form_class = SocialMediaLinksPluginForm
    fields = [
        ("topic", TranslatableField(label=_("Topic"), required=False, initial="")),
        ("text", TranslatableField(label=_("Text"), required=False, initial="")),
        ("icon_size", forms.ChoiceField(label=_("Icon Size"), required=False, choices=[
            ("", "Default"),
            ("lg", "Large"),
            ("2x", "2x"),
            ("3x", "3x"),
            ("4x", "4x"),
            ("5x", "5x"),
        ], initial="")),
        ("alignment", forms.ChoiceField(label=_("Alignment"), required=False, choices=[
            ("", "Default"),
            ("left", "Left"),
            ("center", "Center"),
            ("right", "Right"),
        ], initial="")),
        ("links", forms.ModelMultipleChoiceField(label=_("Links"), required=False,
                                                 queryset=SocialMediaLink.objects.all(),
                                                 )),
    ]

    def get_context_data(self, context):
        links = self.config.get("links", [])
        return {
            "topic": self.get_translated_value("topic"),
            "text": self.get_translated_value("text"),
            "icon_size": self.config.get("icon_size", ""),
            "social_media_links": SocialMediaLink.objects.filter(pk__in=links),
            "alignment": self.config.get("alignment", ""),
        }
