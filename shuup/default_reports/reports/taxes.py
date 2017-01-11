# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import OrderLineTax, Tax
from shuup.default_reports.forms import TaxesReportForm
from shuup.default_reports.mixins import OrderReportMixin
from shuup.reports.report import ShuupReportBase


class TaxesReport(OrderReportMixin, ShuupReportBase):
    identifier = "taxes_report"
    title = _("Taxes")
    form_class = TaxesReportForm

    filename_template = "taxes-report-%(time)s"
    schema = [
        {"key": "tax", "title": _("Tax")},
        {"key": "tax_rate", "title": _("Rate (%)")},
        {"key": "order_count", "title": _("Orders")},
        {"key": "total_charged", "title": _("Total Charged")},
    ]

    def get_objects(self):
        order_line_taxes = OrderLineTax.objects.filter(
            order_line__order__in=super(TaxesReport, self).get_objects()
        )

        tax = self.options.get("tax")
        tax_class = self.options.get("tax_class")

        filters = Q()
        if tax:
            filters &= Q(tax__in=tax)
        if tax_class:
            filters &= Q(order_line__product__tax_class__in=tax_class)

        return order_line_taxes.filter(filters).values(
            "tax", "tax__rate"
        ).annotate(
            total_charged=Sum("amount_value"),
            order_count=Count("order_line__order", distinct=True)
        ).order_by("total_charged")

    def get_data(self):
        data = []
        tax_map = {}

        for tax_total in self.get_objects():
            # load tax on-demand
            if not tax_total["tax"] in tax_map:
                tax_map[tax_total["tax"]] = Tax.objects.get(pk=tax_total["tax"])

            data.append({
                "tax": tax_map[tax_total["tax"]].name,
                "tax_rate": tax_total["tax__rate"] * Decimal(100.0),
                "order_count": tax_total["order_count"],
                "total_charged": self.shop.create_price(tax_total["total_charged"]).as_rounded().value
            })

        return self.get_return_data(data)
