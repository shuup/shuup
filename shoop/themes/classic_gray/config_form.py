# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import itertools

from django import forms
from django.conf import settings
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import get_language

from shoop.xtheme.forms import GenericThemeForm


class ClassicGrayConfigForm(GenericThemeForm):
    def __init__(self, **kwargs):
        super(ClassicGrayConfigForm, self).__init__(**kwargs)
        self._populate_footer_column_order_choices()
        self._populate_cms_page_field()

    def _populate_footer_column_order_choices(self):
        column_mnemonics_to_labels = {
            "cms": _("CMS Page Links"),
            "html": _("Custom HTML"),
            "links": _("Footer Links"),
        }
        column_orders = []
        for x in range(len(column_mnemonics_to_labels)):
            column_orders.extend(itertools.permutations(column_mnemonics_to_labels, x + 1))
        footer_column_order_choices = sorted([
            (
                ",".join(column_order),
                (" / ".join(force_text(column_mnemonics_to_labels[mnem]) for mnem in column_order))
            ) for column_order in column_orders
        ])
        footer_column_order_choices.insert(0, ("", _("None")))
        order_field = self.fields["footer_column_order"]
        order_field.choices = order_field.widget.choices = footer_column_order_choices

    def _populate_cms_page_field(self):
        if "shoop.simple_cms" in settings.INSTALLED_APPS:
            from shoop.simple_cms.models import Page
            self.fields["footer_cms_pages"] = forms.ModelMultipleChoiceField(
                label=_("Footer CMS pages"),
                queryset=Page.objects.translated(get_language()),
                required=False
            )

    def clean(self):
        cleaned_data = super(ClassicGrayConfigForm, self).clean()
        cleaned_data["footer_cms_pages"] = [p.pk for p in cleaned_data.get("footer_cms_pages", ())]
        return cleaned_data
