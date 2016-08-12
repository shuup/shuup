# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.models import Sum
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
        {"key": "total_sales", "title": _("Total Sales")},
    ]

    def get_data(self):
        orders = self.get_objects()
        total_sales_value = orders.aggregate(total=Sum("taxful_total_price_value"))["total"] or 0
        data = [{
            "name": self.shop.name,
            "order_amount": orders.count(),
            "total_sales": self.shop.create_price(total_sales_value),
            "currency": self.shop.currency
        }]
        return self.get_return_data(data)
