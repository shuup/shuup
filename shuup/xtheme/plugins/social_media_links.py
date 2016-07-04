# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import re
from collections import defaultdict

from django import forms
from django.utils.translation import ugettext_lazy as _

from shuup.xtheme import TemplatedPlugin
from shuup.xtheme.plugins.forms import GenericPluginForm, TranslatableField


class SocialMediaLinksPluginForm(GenericPluginForm):
    """
    Form for the social media links xtheme plugin. One field is provided for each
    entry in the plugin's icon_classes attribute, which maps social media site names
    to font-awesome icon classes by default.
    """
    def populate(self):
        """
        Populates form with default plugin fields as well as any social media link type
        included in the plugin's ``icon_classes`` attribute.

        Also adds an ordering field for each link type to change display order.
        """
        icon_classes = self.plugin.icon_classes
        links = self.plugin.config.get("links", {})
        for name, icon_class in sorted(icon_classes.items()):
            url = links[name]["url"] if name in links else ""
            ordering = links[name]["ordering"] if name in links else None
            self.fields[name] = forms.URLField(
                label=name, required=False,
                widget=forms.TextInput(attrs={"placeholder": _("URL")}),
                initial=url)
            self.fields["%s-ordering" % name] = forms.IntegerField(
                label="", required=False, min_value=0, max_value=len(icon_classes)*2,
                initial=ordering, widget=forms.NumberInput(attrs={"placeholder": _("Ordering")}))
        super(SocialMediaLinksPluginForm, self).populate()

    def clean(self):
        """
        Returns cleaned data from default plugin fields and any link fields.

        Processed link configuration information is stored and returned as a dictionary
        (``links``).
        """
        links_dict = defaultdict(dict)
        cleaned_data = {}
        precleaned_data = super(SocialMediaLinksPluginForm, self).clean()
        plugin_fields = [field for (field, value) in self.plugin.fields]
        for field in plugin_fields:
            cleaned_data[field] = precleaned_data.pop(field)
        for link_info in precleaned_data:
            link_name = re.sub("-ordering", "", link_info)
            if not link_info.endswith("-ordering"):
                links_dict[link_name]["url"] = precleaned_data[link_info]
            else:
                links_dict[link_name]["ordering"] = precleaned_data[link_info]
        cleaned_data["links"] = {k: v for (k, v) in links_dict.items() if v.get("url", None)}
        return cleaned_data


class SocialMediaLinksPlugin(TemplatedPlugin):
    """
    An xtheme plugin for displaying site links to common social media sites.
    """
    identifier = "social_media_links"
    name = _("Social Media Links")
    template_name = "shuup/xtheme/plugins/social_media_links.jinja"
    editor_form_class = SocialMediaLinksPluginForm
    fields = [
        ("topic", TranslatableField(label=_("Topic"), required=False, initial="")),
        ("text", TranslatableField(label=_("Title"), required=False, initial="")),
        ("icon_size", forms.ChoiceField(label=_("Icon Size"), required=False, choices=[
            ("", _("Default")),
            ("lg", _("Large")),
            ("2x", "2x"),
            ("3x", "3x"),
            ("4x", "4x"),
            ("5x", "5x"),
        ], initial="")),
        ("alignment", forms.ChoiceField(label=_("Alignment"), required=False, choices=[
            ("", _("Default")),
            ("left", _("Left")),
            ("center", _("Center")),
            ("right", _("Right")),
        ], initial="")),
    ]

    icon_classes = {
        "Facebook": "facebook-square",
        "Flickr": "flickr",
        "Google Plus": "google-plus-square",
        "Instagram": "instagram",
        "Linkedin": "linkedin-square",
        "Pinterest": "pinterest",
        "Tumbler": "tumblr",
        "Twitter": "twitter",
        "Vimeo": "vimeo",
        "Vine": "vine",
        "Yelp": "yelp",
        "Youtube": "youtube",
    }

    def get_context_data(self, context):
        """
        Returns plugin settings and a sorted list of social media links

        :return: Plugin context data
        :rtype: dict
        """
        links = self.get_links()

        return {
            "links": links,
            "request": context["request"],
            "topic": self.get_translated_value("topic"),
            "text": self.get_translated_value("text"),
            "icon_size": self.config.get("icon_size", ""),
            "alignment": self.config.get("alignment", ""),
        }

    def get_links(self):
        """
        Returns the list of social media links sorted according to ordering

        :return: List of link tuples (ordering, icon class, url)
        :rtype: [(int, str, str)]
        """
        links = self.config.get("links", {})

        return sorted([
            (v["ordering"] or 0, self.icon_classes[k], v["url"])
            for (k, v)
            in links.items()
        ])
