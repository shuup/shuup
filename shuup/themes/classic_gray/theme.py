# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import django.conf
from django import forms
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum

from shuup.xtheme import Theme


class ShopLogoAlignment(Enum):
    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"

    class Labels:
        LEFT = _("Left")
        RIGHT = _("Right")
        CENTER = _("Center")


class ClassicGrayTheme(Theme):
    identifier = "shuup.themes.classic_gray"
    name = "Shuup Classic Gray Theme"
    author = "Shuup Team"
    template_dir = "classic_gray"

    fields = [
        ("show_welcome_text", forms.BooleanField(required=False, initial=True, label=_("Show Frontpage Welcome Text"))),
        ("hide_prices", forms.BooleanField(required=False, initial=False, label=_("Hide prices"))),
        ("catalog_mode", forms.BooleanField(required=False, initial=False, label=_("Set shop in catalog mode"))),
        ("shop_logo_width", forms.IntegerField(
            initial=200, max_value=960,
            label=_("Shop logo width"),
            help_text=_("This is the width of the image, in pixels.")
        )),
        ("shop_logo_height", forms.IntegerField(
            initial=80, max_value=500,
            label=_("Shop logo height"),
            help_text=_("This is the height of the image, in pixels.")
        )),
        ("shop_logo_alignment", forms.ChoiceField(
            required=False,
            choices=ShopLogoAlignment.choices(),
            initial=ShopLogoAlignment.LEFT.value,
            label=_("Shop logo alignment")
        )),
        ("shop_logo_aspect_ratio", forms.BooleanField(
            required=False, initial=True,
            label=_("Keep logo aspect ratio"),
            help_text=_("Check this to keep the aspect ratio of the image.")
        ))
    ]

    guide_template = "classic_gray/admin/guide.jinja"
    extra_config_template = "classic_gray/admin/extra_config.jinja"
    extra_config_extra_js = "classic_gray/admin/extra_config_js.jinja"
    extra_config_extra_css = "classic_gray/admin/extra_config_css.jinja"

    stylesheets = [
        {
            "identifier": "default",
            "stylesheet": "shuup/front/css/style.css",
            "name": _("Default"),
            "images": ["shuup/front/img/no_image.png"]
        },
        {
            "identifier": "midnight_blue",
            "stylesheet": "shuup/classic_gray/blue/style.css",
            "name": _("Midnight Blue"),
            "images": ["shuup/front/img/no_image.png"]
        },
        {
            "identifier": "candy_pink",
            "stylesheet": "shuup/classic_gray/pink/style.css",
            "name": _("Candy Pink"),
            "images": ["shuup/front/img/no_image.png"]
        },
    ]

    def get_view(self, view_name):
        import shuup.front.themes.views as views
        return getattr(views, view_name, None)

    def _format_cms_links(self, shop, **query_kwargs):
        if "shuup.simple_cms" not in django.conf.settings.INSTALLED_APPS:
            return
        from shuup.simple_cms.models import Page
        for page in Page.objects.visible(shop).filter(**query_kwargs):
            yield {"url": "/%s" % page.url, "text": force_text(page)}

    def get_cms_navigation_links(self, request):
        return self._format_cms_links(shop=request.shop, visible_in_menu=True)
