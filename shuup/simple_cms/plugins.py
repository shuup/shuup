# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.utils.translation import ugettext_lazy as _

from shuup.simple_cms.models import Page
from shuup.simple_cms.utils import order_query_by_values
from shuup.xtheme import TemplatedPlugin
from shuup.xtheme.plugins.forms import GenericPluginForm, TranslatableField


class OrderedModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def __init__(self, queryset, required=True, widget=None, label=None,
                 initial=None, help_text='', *args, **kwargs):
        super().__init__(
            queryset, required=required, widget=widget, label=label,
            initial=initial, help_text=help_text, *args, **kwargs
        )

        if initial:  # To show current choice order in plugin
            self.queryset = order_query_by_values(self.queryset, initial)

    def _check_values(self, value):  # To save current choice order in DB
        queryset = super(OrderedModelMultipleChoiceField, self)._check_values(value)
        return order_query_by_values(queryset, value)


class PageLinksConfigForm(GenericPluginForm):
    """
    A configuration for the PageLinksPlugin
    """

    def __init__(self, **kwargs):
        super(PageLinksConfigForm, self).__init__(**kwargs)

    def populate(self):
        """
        A custom populate method to display page choices
        """
        for field in self.plugin.fields:
            if isinstance(field, tuple):
                name, value = field
                value.initial = self.plugin.config.get(name, value.initial)
                self.fields[name] = value

        self.fields["pages"] = OrderedModelMultipleChoiceField(
            queryset=Page.objects.visible(self.request.shop),
            required=False,
            initial=self.plugin.config.get("pages", None),
        )

    def clean(self):
        """
        A custom clean method to save page configuration information in a serializable form
        """
        cleaned_data = super(PageLinksConfigForm, self).clean()
        pages = cleaned_data.get("pages", [])
        cleaned_data["pages"] = [page.pk for page in pages if hasattr(page, "pk")]
        return cleaned_data


class PageLinksPlugin(TemplatedPlugin):
    """
    A plugin for displaying links to visible CMS pages in the shop front
    """
    identifier = "simple_cms.page_links"
    name = _("CMS Page Links")
    template_name = "shuup/simple_cms/plugins/page_links.jinja"
    editor_form_class = PageLinksConfigForm
    fields = [
        ("title", TranslatableField(label=_("Title"), required=False, initial="")),
        ("show_all_pages", forms.BooleanField(
            label=_("Show all pages"),
            required=False,
            initial=True,
            help_text=_("All pages are shown, even if not selected"),
        )),
        ("hide_expired", forms.BooleanField(
            label=_("Hide expired pages"),
            initial=False,
            required=False,
        )),
        "pages",
    ]

    def get_context_data(self, context):
        """
        A custom get_context_data method to return pages, possibly filtering expired pages
        based on the plugin's ``hide_expired`` setting
        """
        selected_pages = self.config.get("pages", [])
        show_all_pages = self.config.get("show_all_pages", True)
        hide_expired = self.config.get("hide_expired", False)

        pages_qs = Page.objects.prefetch_related("translations").not_deleted()

        if hide_expired:
            pages_qs = pages_qs.visible(context["request"].shop, user=context["request"].user)
        else:
            pages_qs = pages_qs.for_shop(context["request"].shop).for_user(user=context["request"].user)

        if not show_all_pages:
            pages_qs = pages_qs.filter(id__in=selected_pages)

        pages_qs = order_query_by_values(pages_qs, selected_pages)

        return {
            "title": self.get_translated_value("title"),
            "pages": pages_qs,
        }
