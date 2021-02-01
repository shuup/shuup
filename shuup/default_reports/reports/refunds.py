# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import OrderLineType
from shuup.default_reports.forms import OrderReportForm
from shuup.default_reports.mixins import OrderReportMixin
from shuup.reports.report import ShuupReportBase
from shuup.utils.money import Money


class RefundedSalesReport(OrderReportMixin, ShuupReportBase):
    identifier = "refunded-sales"
    title = _("Refunded Sales")
    filename_template = "refunded-sales-%(time)s"
    form_class = OrderReportForm

    schema = [
        {"key": "refunded_orders", "title": _("Refunded Orders")},
        {"key": "total_refunded", "title": _("Total Refunded")},
    ]

    def get_data(self, **kwargs):
        orders = super(RefundedSalesReport, self).get_objects().filter(lines__type=OrderLineType.REFUND).distinct()
        total_refunded = Money(0, self.shop.currency)

        for order in orders:
            total_refunded += order.get_total_refunded_amount()

        data = [{
            "refunded_orders": len(orders),
            "total_refunded": total_refunded.value
        }]
        return self.get_return_data(data, has_totals=False)
