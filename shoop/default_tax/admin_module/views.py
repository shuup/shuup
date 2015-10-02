# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _, string_concat

from shoop.admin.utils.picotable import Column
from shoop.admin.utils.views import CreateOrUpdateView, PicotableListView
from shoop.default_tax.models import TaxRule
from shoop.utils.patterns import PATTERN_SYNTAX_HELP_TEXT


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
        help_texts = {
            "country_codes_pattern": string_concat(
                PATTERN_SYNTAX_HELP_TEXT,
                " ",
                _("Use ISO 3166-1 country codes (US, FI etc.)")
            ),
            "region_codes_pattern": PATTERN_SYNTAX_HELP_TEXT,
            "postal_codes_pattern": PATTERN_SYNTAX_HELP_TEXT,
        }

    def clean(self):
        data = super(TaxRuleForm, self).clean()
        data["country_codes_pattern"] = data["country_codes_pattern"].upper()
        return data


class TaxRuleEditView(CreateOrUpdateView):
    model = TaxRule
    template_name = "shoop/default_tax/admin/edit.jinja"
    form_class = TaxRuleForm
    context_object_name = "tax_rule"
    add_form_errors_as_messages = True


class TaxRuleListView(PicotableListView):
    model = TaxRule

    columns = [
        Column("tax", _(u"Tax")),
        Column("priority", _(u"Priority")),
        Column("enabled", _(u"Enabled")),
    ]
