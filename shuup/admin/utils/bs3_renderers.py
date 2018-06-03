# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from bootstrap3.renderers import FieldRenderer
from bootstrap3.utils import add_css_class
from django.forms import DateField, DateTimeField, ModelMultipleChoiceField
from django.utils.translation import ugettext_lazy as _


class AdminFieldRenderer(FieldRenderer):

    def __init__(self, field, **kwargs):
        self.render_label = bool(kwargs.pop("render_label", True))
        self.set_placeholder = bool(kwargs.pop("set_placeholder", True))
        self.widget_class = kwargs.pop("widget_class", None)
        default_show_help_block = True
        if isinstance(field.field, ModelMultipleChoiceField):
            if not self.widget_class:
                self.widget_class = "multiselect"
        if isinstance(field.field, DateTimeField):
            if not self.widget_class:
                self.widget_class = "datetime"
        if isinstance(field.field, DateField):
            if not self.widget_class:
                self.widget_class = "date"
        self.show_help_block = bool(kwargs.pop("show_help_block", default_show_help_block))

        kwargs["required_css_class"] = "required-field"
        kwargs["set_required"] = False
        kwargs["bound_css_class"] = " "  # This is a hack, but Django-Bootstrap is silly and requires a truthy value.
        super(AdminFieldRenderer, self).__init__(field, **kwargs)
        if not self.set_placeholder:
            self.placeholder = None

    def get_label(self):
        if not self.render_label:
            return None
        return super(AdminFieldRenderer, self).get_label()

    def add_class_attrs(self, *args, **kwargs):
        widget = kwargs.get('widget') or self.widget
        super(AdminFieldRenderer, self).add_class_attrs(*args, **kwargs)
        if self.widget_class:
            classes = widget.attrs.get('class', '')
            classes = add_css_class(classes, self.widget_class)
            widget.attrs['class'] = classes

    def add_help_attrs(self, *args, **kwargs):
        widget = kwargs.get('widget') or self.widget
        super(AdminFieldRenderer, self).add_help_attrs(*args, **kwargs)
        if not widget.attrs.get("title"):
            widget.attrs.pop("title", None)  # Remove the empty attribute

        if not self.show_help_block:  # Remove field help to avoid rendering `help-block`
            self.field_help = ''

    def append_to_field(self, html):
        if self.field_help:
            if self.field.field.required:
                self.field_help = _("Required. %s" % self.field_help)
            else:
                self.field_help = _("Optional. %s" % self.field_help)
            html += "<span class='help-popover-btn'>"
            # tabindex is required for popover to function but we don't actually want to be able to tab to it
            # so set a large tabindex
            html += "<a class=\"btn\" data-toggle=\"popover\" data-placement=\"bottom\" "
            html += "role=\"button\" tabindex=\"50000\" "
            html += "data-html=\"true\" data-trigger=\"focus\" title=\"{title}\" data-content=\"{help}\">".format(
                title=self.field.label, help=self.field_help)
            html += "<i class='fa fa-question-circle'></i>"
            html += "</a>"
            html += "</span>"
        if self.field_errors:
            errors = "<br>".join(self.field_errors)
            html += '<div class="help-block error-block">{error}</div>'.format(error=errors)
        return html
