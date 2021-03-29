# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.models import Avg, Count, Sum
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import Contact
from shuup.default_reports.forms import CustomerSalesReportForm
from shuup.default_reports.mixins import OrderReportMixin
from shuup.reports.report import ShuupReportBase


class CustomerSalesReport(OrderReportMixin, ShuupReportBase):
    identifier = "customer_sales_report"
    title = _("Customer Sales")
    form_class = CustomerSalesReportForm

    filename_template = "customer-sales-report-%(time)s"
    schema = [
        {"key": "customer", "title": _("Customer")},
        {"key": "order_count", "title": _("Orders")},
        {"key": "average_sales", "title": _("Average Sales")},
        {"key": "taxless_total", "title": _("Taxless Total")},
        {"key": "taxful_total", "title": _("Taxful Total")},
    ]

    def get_objects(self):
        return (
            Contact.objects.filter(customer_orders__in=super(CustomerSalesReport, self).get_objects())
            .annotate(
                order_count=Count("customer_orders", distinct=True),
                average_sales=Avg("customer_orders__taxful_total_price_value"),
                taxless_total=Sum("customer_orders__taxless_total_price_value"),
                taxful_total=Sum("customer_orders__taxful_total_price_value"),
            )
            .filter(order_count__gt=0)
            .order_by("-%s" % self.options["order_by"])[: self.queryset_row_limit]
            .values("name", "order_count", "average_sales", "taxless_total", "taxful_total")
        )

    def get_data(self):
        data = []

        for contact in self.get_objects():
            data.append(
                {
                    "customer": contact["name"],
                    "order_count": contact["order_count"],
                    "average_sales": self.shop.create_price(contact["average_sales"]).as_rounded().value,
                    "taxless_total": self.shop.create_price(contact["taxless_total"]).as_rounded().value,
                    "taxful_total": self.shop.create_price(contact["taxful_total"]).as_rounded().value,
                }
            )

        return self.get_return_data(data)
