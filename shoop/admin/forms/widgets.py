# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.forms import HiddenInput, Widget
from django.utils.encoding import force_text
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from filer.models import File

from shoop.admin.utils.forms import flatatt_filter
from shoop.admin.utils.urls import get_model_url, NoModelUrl
from shoop.core.models import Product


class BasePopupChoiceWidget(Widget):
    browse_kind = None
    filter = None

    def __init__(self, attrs=None, clearable=False, empty_text=u"\u2014"):
        self.clearable = clearable
        self.empty_text = empty_text
        super(BasePopupChoiceWidget, self).__init__(attrs)

    def get_browse_markup(self):
        icon = "<i class='fa fa-folder'></i>"
        return "<button class='browse-btn btn btn-info btn-sm' type='button'>%(icon)s %(text)s</button>" % {
            "icon": icon,
            "text": _("Browse")
        }

    def get_clear_markup(self):
        icon = "<i class='fa fa-cross'></i>"
        return "<button class='clear-btn btn btn-default btn-sm' type='button'>%(icon)s %(text)s</button>" % {
            "icon": icon,
            "text": _("Clear")
        }

    def render_text(self, obj):
        url = getattr(obj, "url", None)
        text = self.empty_text
        if obj:
            text = force_text(obj)
            if not url:
                try:
                    url = get_model_url(obj)
                except NoModelUrl:
                    pass
        if not url:
            url = "#"

        return mark_safe("<a class=\"browse-text\" href=\"%(url)s\" target=\"_blank\">%(text)s</a>&nbsp;" % {
            "text": escape(text),
            "url": escape(url),
        })

    def get_object(self, value):
        raise NotImplementedError("Not implemented")

    def render(self, name, value, attrs=None):
        if value:
            obj = self.get_object(value)
        else:
            obj = None
        pk_input = HiddenInput().render(name, value, attrs)
        media_text = self.render_text(obj)
        bits = [self.get_browse_markup(), pk_input, " ", media_text]

        if self.clearable:
            bits.insert(1, self.get_clear_markup())

        return mark_safe("<div %(attrs)s>%(content)s</div>" % {
            "attrs": flatatt_filter({
                "class": "browse-widget %s-browse-widget" % self.browse_kind,
                "data-browse-kind": self.browse_kind,
                "data-clearable": self.clearable,
                "data-empty-text": self.empty_text,
                "data-filter": self.filter
            }),
            "content": "".join(bits)
        })


class MediaChoiceWidget(BasePopupChoiceWidget):
    browse_kind = "media"

    def get_object(self, value):
        return File.objects.get(pk=value)


class ImageChoiceWidget(MediaChoiceWidget):
    filter = "images"


class ProductChoiceWidget(BasePopupChoiceWidget):
    browse_kind = "product"

    def get_object(self, value):
        return Product.objects.get(pk=value)
