# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.utils.translation import ugettext_lazy as _

from shuup.front.apps.carousel.models import Carousel
from shuup.xtheme import TemplatedPlugin
from shuup.xtheme.plugins.forms import TranslatableField

from .forms import CarouselConfigForm


class CarouselPlugin(TemplatedPlugin):
    identifier = "shuup.front.apps.carousel.carousel"
    name = _("Carousel Plugin")
    template_name = "shuup/carousel/carousel.jinja"
    cacheable = True
    fields = [
        ("carousel", None),
        (
            "render_image_text",
            forms.BooleanField(
                label=_("Render image text"),
                required=False,
                initial=True,
                help_text=_("Display the text on top of the image."),
            ),
        ),
    ]
    editor_form_class = CarouselConfigForm

    def get_defaults(self):
        defaults = super(CarouselPlugin, self).get_defaults()
        defaults.update({"carousel": self.config.get("carousel", None), "active": self.config.get("active", True)})
        return defaults

    def get_cache_key(self, context, **kwargs) -> str:
        carousel_id = self.config.get("carousel")
        active = self.config.get("active")
        return str((carousel_id, active))

    def get_context_data(self, context):
        """
        Use only slides that has translated image in current language

        :param context: current context
        :return: updated plugin context
        :rtype: dict
        """
        request = context["request"]
        carousel_id = self.config.get("carousel")
        active = self.config.get("active")
        return {
            "request": request,
            "carousel": Carousel.objects.filter(id=carousel_id, shops=request.shop).first() if carousel_id else None,
            "active": active,
            "type": "carousel",
        }


class BannerBoxPlugin(CarouselPlugin):
    identifier = "shuup.front.apps.carousel.banner_box"
    name = _("Banner Box")
    editor_form_class = CarouselConfigForm
    fields = [
        ("title", TranslatableField(label=_("Title"), required=False, initial="")),
        (
            "render_image_text",
            forms.BooleanField(
                label=_("Render image text"),
                required=False,
                initial=True,
                help_text=_("Display the text on top of the image."),
            ),
        ),
    ]

    def get_context_data(self, context):
        """
        Add title from config to context data

        :param context: Current context
        :return: updated Plugin context
        :rtype: dict
        """
        data = super(BannerBoxPlugin, self).get_context_data(context)
        data["title"] = self.get_translated_value("title")
        data["type"] = "banner_box"
        return data
