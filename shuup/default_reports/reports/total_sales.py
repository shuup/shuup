# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.models import Avg, Count, Sum
from django.utils.translation import ugettext_lazy as _

from shuup.default_reports.forms import OrderReportForm
from shuup.default_reports.mixins import OrderReportMixin
from shuup.reports.report import ShuupReportBase


class TotalSales(OrderReportMixin, ShuupReportBase):
    identifier = "total_sales_report"
    title = _("Total Sales")
    form_class = OrderReportForm

    filename_template = "total-sales-%(time)s"
    schema = [
        {"key": "name", "title": _("Shop Name")},
        {"key": "currency", "title": _("Currency")},
        {"key": "order_amount", "title": _("Order Amount")},
        {"key": "customers", "title": _("Customers")},
        {"key": "customer_avg_sale", "title": _("Customer Average Sale")},
        {"key": "total_sales", "title": _("Total Sales")},
    ]

    def get_data(self):
        orders = self.get_objects()
        aggregation = orders.aggregate(
            customers=Count("customer", distinct=True),
            total=Sum("taxful_total_price_value"),
            avg_sale=Avg("taxful_total_price_value")
        )
        total_sales_value = aggregation["total"] or 0
        customer_avg_sale = aggregation["avg_sale"] or 0
        customers = aggregation["customers"] or 0

        data = [{
            "name": self.shop.name,
            "order_amount": orders.count(),
            "customers": customers,
            "customer_avg_sale": self.shop.create_price(customer_avg_sale).as_rounded().value,
            "total_sales": self.shop.create_price(total_sales_value).as_rounded().value,
            "currency": self.shop.currency
        }]
        return self.get_return_data(data)
