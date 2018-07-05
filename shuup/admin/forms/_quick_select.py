# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.urlresolvers import NoReverseMatch
from django.forms import Select, SelectMultiple
from django.forms.utils import flatatt
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


class QuickAddRelatedObjectSelectBase(Select):
    def __init__(self, attrs=None, choices=(), editable_model=None):
        self.editable_model = editable_model
        if editable_model:
            edit_model_attr = {"data-edit-model": editable_model}

            if attrs:
                attrs.update(edit_model_attr)
            else:
                attrs = edit_model_attr
        super(QuickAddRelatedObjectSelectBase, self).__init__(attrs, choices)


class QuickAddRelatedObjectSelect(QuickAddRelatedObjectSelectBase):
    url = ""
    model = ""
    template_name = "shuup/admin/forms/widgets/quick_add_select.jinja"

    def get_context(self, name, value, attrs):
        context = super(QuickAddRelatedObjectSelect, self).get_context(name, value, attrs)
        context["quick_add_model"] = self.model
        try:
            context["quick_add_url"] = "{}?mode=iframe&quick_add_target={}".format(force_text(self.url), name)
        except NoReverseMatch:
            pass
        context["quick_add_btn_title"] = _("Create New")
        return context


class QuickAddRelatedObjectMultiSelect(SelectMultiple):
    url = ""
    template_name = "shuup/admin/forms/widgets/quick_add_select.jinja"

    def get_context(self, name, value, attrs):
        attrs["multiple"] = True
        context = super(QuickAddRelatedObjectMultiSelect, self).get_context(name, value, attrs)

        try:
            context["quick_add_url"] = "{}?mode=iframe&quick_add_target={}".format(force_text(self.url), name)
        except NoReverseMatch:
            pass

        context["quick_add_btn_title"] = _("Create New")
        return context


class QuickAddRelatedObjectSelectWithoutTemplate(QuickAddRelatedObjectSelectBase):
    """
    Old implementation for Django 1.9 and 1.8 where the select
    still has the render.
    """
    url = ""
    model = ""

    def render(self, name, value, attrs=None, choices=()):
        # make sure the url exists
        try:
            url = force_text(self.url)
        except NoReverseMatch:
            url = None

        if not url:
            return ""

        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, name=name)
        if self.model:
            final_attrs['data-model'] = self.model
            choices = []
        output = [format_html('<select{}>', flatatt(final_attrs))]
        options = self.render_options(choices, [value])
        if options:
            output.append(options)
        output.append('</select>')
        quick_add_button = """
            <span class="quick-add-btn">
                <a
                    class="btn"
                    data-url="%s?mode=iframe&quick_add_target=%s"
                    data-toggle="popover"
                    data-placement="bottom"
                    data-trigger="manual"
                    data-content="%s">
                        <i class="fa fa-plus text-primary"></i>
                </a>
            </span>
        """.strip()
        output.append(quick_add_button % (self.url, name, _("Create New")))
        return mark_safe('\n'.join(output))


class QuickAddRelatedObjectMultiSelectWithoutTemplate(SelectMultiple):
    """
    Old implementation for Django 1.9 and 1.8 where the select
    still has the render.
    """
    url = ""

    def render(self, name, value, attrs=None, choices=()):
        # make sure the url exists
        try:
            url = force_text(self.url)
        except NoReverseMatch:
            url = None

        if not url:
            return ""

        if value is None:
            value = []
        final_attrs = self.build_attrs(attrs, name=name)
        output = [format_html('<select multiple="multiple"{}>', flatatt(final_attrs))]
        options = self.render_options(choices, value)
        if options:
            output.append(options)
        output.append('</select>')
        quick_add_button = """
            <span class="quick-add-btn">
                <a
                    class="btn"
                    data-url="%s?mode=iframe&quick_add_target=%s"
                    data-toggle="popover"
                    data-placement="bottom"
                    data-trigger="hover"
                    data-content="%s">
                        <i class="fa fa-plus text-primary"></i>
                </a>
            </span>
        """.strip()
        output.append(quick_add_button % (self.url, name, _("Create New")))
        return mark_safe('\n'.join(output))
