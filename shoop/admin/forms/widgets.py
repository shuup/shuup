# -*- coding: utf-8 -*-
from django.forms import HiddenInput, Widget
from django.utils.encoding import force_text
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from filer.models import File
from shoop.admin.utils.urls import get_model_url, NoModelUrl


class BasePopupChoiceWidget(Widget):
    browse_kind = None

    def get_browse_markup(self):
        icon = "<i class='fa fa-folder'></i>"
        return "<button class='browse-btn btn btn-info btn-sm' type='button'>%(icon)s %(text)s</button>" % {
            "icon": icon,
            "text": _("Browse")
        }

    def render_text(self, obj):
        url = getattr(obj, "url", None)
        text = u"\u2014"
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
        bits = "".join([pk_input, media_text, self.get_browse_markup()])
        return mark_safe("<div class='browse-widget' data-browse-kind='%(browse_kind)s'>%(bits)s</div>" % {
            "browse_kind": self.browse_kind,
            "bits": bits
        })


class MediaChoiceWidget(BasePopupChoiceWidget):
    browse_kind = "media"
    def get_object(self, value):
        return File.objects.get(pk=value)
