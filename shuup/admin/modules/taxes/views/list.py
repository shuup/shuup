# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shuup.admin.utils.picotable import (
    Column, TextFilter, true_or_false_filter
)
from shuup.admin.utils.views import PicotableListView
from shuup.core.models import CustomerTaxGroup, Tax, TaxClass
from shuup.utils.i18n import format_percent


def _format_rate(tax_rule):
    if tax_rule.rate is None:
        return ""
    return format_percent(tax_rule.rate, digits=3)


class TaxListView(PicotableListView):
    model = Tax

    default_columns = [
        Column(
            "name", _("Name"), sort_field="translations__name",
            filter_config=TextFilter(
                filter_field="translations__name",
                placeholder=_("Filter by name..."),
            ),
        ),
        Column("code", _(u"Code")),
        Column("rate", _("Rate"), display=_format_rate),
        # Column("amount", _(u"Amount")),
        Column("enabled", _(u"Enabled"), filter_config=true_or_false_filter),
    ]
    toolbar_buttons_provider_key = "tax_list_toolbar_provider"
    mass_actions_provider_key = "tax_list_mass_actions_provider"


class CustomerTaxGroupListView(PicotableListView):
    model = CustomerTaxGroup

    default_columns = [
        Column(
            "name", _("Name"), sort_field="translations__name",
            filter_config=TextFilter(
                filter_field="translations__name",
                placeholder=_("Filter by name..."),
            ),
        ),
    ]


class TaxClassListView(PicotableListView):
    model = TaxClass

    default_columns = [
        Column(
            "name", _("Name"), sort_field="translations__name",
            filter_config=TextFilter(
                filter_field="translations__name",
                placeholder=_("Filter by name..."),
            ),
        ),
    ]
