# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
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


class NoModel(object):
    def __nonzero__(self):
        return False

    __bool__ = __nonzero__


class QuickAddRelatedObjectBaseMixin(object):
    model = NoModel()
    url = None

    def __init__(self, attrs=None, choices=(), editable_model=None):
        attrs = attrs or {}
        self.editable_model = editable_model
        if editable_model:
            attrs.update({"data-edit-model": editable_model})
        super(QuickAddRelatedObjectBaseMixin, self).__init__(attrs, choices)


class QuickAddRelatedObjectSelectMixin(QuickAddRelatedObjectBaseMixin):
    def __init__(self, attrs=None, choices=(), editable_model=None, initial=None, model=None):
        """
        :param initial int: primary key of the object that is initially selected
        """
        if model is not None:
            self.model = model

        if self.model and initial:
            choices = [(initial.pk, force_text(initial))]

        super(QuickAddRelatedObjectSelectMixin, self).__init__(attrs, choices, editable_model)


class QuickAddRelatedObjectMultipleSelectMixin(QuickAddRelatedObjectBaseMixin):
    def __init__(self, attrs=None, choices=(), editable_model=None, initial=None, model=None):
        """
        :param initial list[int]: list of primary keys of the objects that
            are initially selected
        """
        if model is not None:
            self.model = model

        if self.model and initial:
            choices = [(instance.pk, force_text(instance)) for instance in initial]

        super(QuickAddRelatedObjectMultipleSelectMixin, self).__init__(attrs, choices, editable_model)


class QuickAddRelatedObjectSelect(QuickAddRelatedObjectSelectMixin, Select):
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


class QuickAddRelatedObjectMultiSelect(QuickAddRelatedObjectMultipleSelectMixin, SelectMultiple):
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


class QuickAddRelatedObjectSelectWithoutTemplate(QuickAddRelatedObjectSelectMixin, Select):
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
                    class="btn btn-inverse"
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


class QuickAddRelatedObjectMultiSelectWithoutTemplate(QuickAddRelatedObjectMultipleSelectMixin, SelectMultiple):
    """
    Old implementation for Django 1.9 and 1.8 where the `select`
    still has the `render`.
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
                    class="btn btn-inverse"
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
