# -*- coding: utf-8 -*-
from django.forms import HiddenInput, Widget
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.html import escape
from filer.models import File


class MediaChoiceWidget(Widget):
    BROWSE_MARKUP = "<button class='media-browse btn btn-sm' type='button'><i class='fa fa-folder'></i> Browse</button>"

    def render_text(self, obj):
        if obj:
            text = force_text(obj)
            url = obj.url
        else:
            text = u"\u2014"
            url = "about:blank"

        return mark_safe("<a class=\"media-text\" href=\"%(url)s\" target=\"_blank\">%(text)s</a>&nbsp;" % {
            "text": escape(text),
            "url": escape(url),
        })

    def render(self, name, value, attrs=None):
        if value:
            obj = File.objects.get(pk=value)
        else:
            obj = None
        pk_input = HiddenInput().render(name, value, attrs)
        media_text = self.render_text(obj)
        bits = "".join([pk_input, media_text, self.BROWSE_MARKUP])
        return mark_safe("<div class='media-widget'>%s</div>" % bits)

