# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.forms import Select, SelectMultiple
from django.forms.utils import flatatt
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


class QuickAddRelatedObjectSelect(Select):
    url = ""
    model = ""
    template_name = "shuup/admin/forms/widgets/quick_add_select.jinja"

    def get_context(self, name, value, attrs):
        context = super(QuickAddRelatedObjectSelect, self).get_context(name, value, attrs)
        context["quick_add_model"] = self.model
        context["quick_add_url"] = "{}?mode=iframe&quick_add_target={}".format(self.url, name)
        context["quick_add_btn_title"] = _("Create New")
        return context


class QuickAddRelatedObjectMultiSelect(SelectMultiple):
    url = ""
    template_name = "shuup/admin/forms/widgets/quick_add_select.jinja"

    def get_context(self, name, value, attrs):
        attrs["multiple"] = True
        context = super(QuickAddRelatedObjectMultiSelect, self).get_context(name, value, attrs)
        context["quick_add_url"] = "{}?mode=iframe&quick_add_target={}".format(self.url, name)
        context["quick_add_btn_title"] = _("Create New")
        return context


class QuickAddRelatedObjectSelectWithoutTemplate(Select):
    """
    Old implementation for Django 1.9 and 1.8 where the select
    still has the render.
    """
    url = ""
    model = ""

    def render(self, name, value, attrs=None, choices=()):
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
