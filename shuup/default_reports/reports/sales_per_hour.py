# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import itertools
import six
from django.utils.timezone import localtime
from django.utils.translation import ugettext_lazy as _

from shuup.default_reports.forms import OrderReportForm
from shuup.default_reports.mixins import OrderReportMixin
from shuup.reports.report import ShuupReportBase


class SalesPerHour(OrderReportMixin, ShuupReportBase):
    identifier = "sales-per-hour"
    title = _("Sales Per Hour")
    filename_template = "sales-per-hour-%(time)s"
    form_class = OrderReportForm

    schema = [
        {"key": "hour", "title": _("Hour")},
        {"key": "order_amount", "title": _("Order Amount")},
        {"key": "total_sales", "title": _("Total Sales")},
    ]

    def date_hour(self, timestamp):
        return localtime(timestamp).strftime("%H")

    def get_data(self, **kwargs):
        orders = self.get_objects()
        groups = itertools.groupby(orders, lambda x: self.date_hour(x.order_date))
        data = []
        hour_data = {}
        for base_hour in range(0, 24):
            hour_data[base_hour] = {"hour": base_hour, "order_amount": 0, "total_sales": 0}
        for hour, matches in groups:
            total = 0
            amount = 0
            for match in matches:
                amount += 1
                total += match.taxful_total_price_value

            hour = int(hour)
            hour_data[hour]["order_amount"] = amount
            hour_data[hour]["total_sales"] = self.shop.create_price(total).as_rounded().value

        for hour, hourly_data in sorted(six.iteritems(hour_data)):
            data.append(hourly_data)

        return self.get_return_data(data, has_totals=False)
