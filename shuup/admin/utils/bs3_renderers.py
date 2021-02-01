# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from bootstrap3.renderers import FieldRenderer
from bootstrap3.utils import add_css_class
from django.forms import DateField, DateTimeField, ModelMultipleChoiceField


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
            field.field.widget.attrs["readonly"] = ""  # Make datetime fields readonly
            if not self.widget_class:
                self.widget_class = "datetime"
        if isinstance(field.field, DateField):
            if not self.widget_class:
                self.widget_class = "date"
        self.show_help_block = bool(kwargs.pop("show_help_block", default_show_help_block))

        kwargs["required_css_class"] = "required-field"
        kwargs["set_required"] = False
        kwargs["bound_css_class"] = " "  # This is a hack, but Django-Bootstrap is silly and requires a truthy value.
        if "form_group_class" not in kwargs:
            kwargs["form_group_class"] = "form-group form-content"
        kwargs["field_class"] = "form-input-group d-flex position-relative"
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
        from django.template import loader as template_loader
        edit_button = template_loader.render_to_string("shuup/admin/forms/widgets/edit_button.jinja", {"field": self})
        help_text = template_loader.render_to_string("shuup/admin/forms/widgets/help_text.jinja", {"field": self})
        return "".join([html, edit_button.strip(), help_text.strip()])
