# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shoop.admin.utils.picotable import (
    Column, TextFilter, true_or_false_filter
)
from shoop.admin.utils.views import PicotableListView
from shoop.core.models import CustomerTaxGroup, Tax, TaxClass
from shoop.utils.i18n import format_percent


def _format_rate(tax_rule):
    if tax_rule.rate is None:
        return ""
    return format_percent(tax_rule.rate, digits=3)


class TaxListView(PicotableListView):
    model = Tax

    columns = [
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


class CustomerTaxGroupListView(PicotableListView):
    model = CustomerTaxGroup

    columns = [
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

    columns = [
        Column(
            "name", _("Name"), sort_field="translations__name",
            filter_config=TextFilter(
                filter_field="translations__name",
                placeholder=_("Filter by name..."),
            ),
        ),
    ]
