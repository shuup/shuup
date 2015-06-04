# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
from django import forms
from django.utils.translation import ugettext_lazy as _
from shoop.admin.utils.forms import add_form_errors_as_messages
from shoop.admin.utils.picotable import Column
from shoop.admin.utils.views import CreateOrUpdateView, PicotableListView, add_create_or_change_message
from shoop.default_tax.models import TaxRule


class TaxRuleForm(forms.ModelForm):
    class Meta:
        model = TaxRule
        fields = [
            "tax",
            "tax_classes",
            "customer_tax_groups",
            "country_codes_pattern",
            "region_codes_pattern",
            "postal_codes_pattern",
            "enabled",
            "priority",
        ]


class TaxRuleEditView(CreateOrUpdateView):
    model = TaxRule
    template_name = "shoop/default_tax/admin/edit.jinja"
    form_class = TaxRuleForm
    context_object_name = "tax_rule"

    def form_valid(self, form):
        add_create_or_change_message(self.request, self.object, is_new=(not self.object.pk))
        return super(TaxRuleEditView, self).form_valid(form)

    def form_invalid(self, form):
        add_form_errors_as_messages(self.request, form)
        return super(TaxRuleEditView, self).form_invalid(form)


class TaxRuleListView(PicotableListView):
    model = TaxRule

    columns = [
        Column("tax", _(u"Tax")),
        Column("priority", _(u"Priority")),
        Column("enabled", _(u"Enabled")),
    ]
