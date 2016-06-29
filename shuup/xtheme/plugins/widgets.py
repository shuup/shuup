# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from shuup.utils.i18n import get_language_name
from shuup.xtheme.plugins.consts import FALLBACK_LANGUAGE_CODE


class TranslatableFieldWidget(forms.Widget):
    # This implementation is definitely inspired by forms.MultiWidget.

    def __init__(self, languages, input_widget=forms.TextInput, attrs=None):
        super(TranslatableFieldWidget, self).__init__(attrs)
        self.languages = languages
        self.input_widget = input_widget
        if not callable(self.input_widget):  # pragma: no cover
            raise ValueError("%r's input_widget must be callable" % self)

    def render(self, name, value, attrs=None):
        value_dict = self.decompress(value)
        output = []
        final_attrs = self.build_attrs(attrs)
        id_ = final_attrs.get('id', None)
        for language_code in self._iter_languages():
            widget = self._build_widget(language_code)
            widget.is_localized = self.is_localized
            widget_value = value_dict.get(language_code)
            if id_:
                final_attrs = dict(final_attrs, id='%s_%s' % (id_, language_code))
            html = widget.render(name + '_%s' % language_code, widget_value, final_attrs)
            output.append((language_code, final_attrs.get("id"), html))
        return mark_safe(self.format_output(output))

    def _iter_languages(self):
        return (list(self.languages) + [FALLBACK_LANGUAGE_CODE])

    def _build_widget(self, language):
        return self.input_widget()

    def id_for_label(self, id_):
        # See the comment for RadioSelect.id_for_label()
        if id_:
            id_ += '_%s' % self.languages[0]
        return id_

    def value_from_datadict(self, data, files, name):
        out_dict = {}
        widget = self._build_widget(None)
        for language_code in self._iter_languages():
            value = widget.value_from_datadict(data, files, name + '_%s' % language_code)
            if value not in (None, ""):
                out_dict[language_code] = value
        if not out_dict:
            # Fallback: If the dictionary remained empty to this stage,
            # see if it's "just there", and if so, call it the fallback.
            value = widget.value_from_datadict(data, files, name)
            if value not in (None, ""):
                out_dict[FALLBACK_LANGUAGE_CODE] = value
        return out_dict

    def format_output(self, widget_pairs):
        rendered_table = ["<table><tbody>"]
        for language_code, id, html in widget_pairs:
            rendered_table.append("<tr><td><label for=\"%(id)s\">%(language_name)s</td><td>%(html)s</td></tr>\n" % {
                "id": id,
                "language_name": (
                    get_language_name(language_code)
                    if language_code != FALLBACK_LANGUAGE_CODE
                    else _("(Untranslated)")
                ),
                "html": html
            })
        rendered_table.append("</tbody></table>")

        return ''.join(rendered_table)

    def decompress(self, value):
        out_dict = {}
        if value is None:
            return out_dict
        if isinstance(value, dict):
            out_dict.update(value)
        else:
            out_dict[FALLBACK_LANGUAGE_CODE] = value
        return out_dict


class XThemeModelChoiceWidget(forms.Select):
    def render(self, name, value, attrs=None, choices=()):
        return mark_safe(
            render_to_string("shuup/xtheme/_model_widget.jinja", {
                "name": name,
                "selected_value": value,
                "objects": self.choices,
            })
        )


class XThemeModelChoiceField(forms.ModelChoiceField):
    widget = XThemeModelChoiceWidget

    def label_from_instance(self, obj):
        return obj
