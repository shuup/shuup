# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import itertools

from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import OrderLine
from shuup.default_reports.forms import ShippingReportForm
from shuup.default_reports.mixins import OrderReportMixin
from shuup.reports.report import ShuupReportBase


class ShippingReport(OrderReportMixin, ShuupReportBase):
    identifier = "shipping_report"
    title = _("Shipping")
    form_class = ShippingReportForm

    filename_template = "shipping-report-%(time)s"
    schema = [
        {"key": "carrier", "title": _("Carrier")},
        {"key": "shipping_method", "title": _("Shipping method")},
        {"key": "order_count", "title": _("Orders")},
        {"key": "total_charged", "title": _("Total Charged")},
    ]

    def get_objects(self):
        shipping_method = self.options.get("shipping_method")
        carrier = self.options.get("carrier")

        filters = Q()
        if shipping_method:
            filters &= Q(shipping_method__in=shipping_method)
        if carrier:
            filters &= Q(shipping_method__carrier__in=carrier)

        orders = super(ShippingReport, self).get_objects().filter(filters)
        order_lines = OrderLine.objects.shipping().filter(order__in=orders)

        return order_lines.select_related(
            "order__shipping_method__carrier"
        ).only(
            "order__shipping_method_name",
            "order__shipping_method__carrier",
            "base_unit_price_value",
            "discount_amount_value",
            "quantity"
        ).order_by("order__shipping_method__carrier_id", "order__shipping_method_id")

    def get_data(self):
        data = []

        # just return a tuple (carrier_ID, shipping_method_ID)
        get_group_func = (lambda ol: (ol.order.shipping_method.carrier_id, ol.order.shipping_method_id))

        for key, group in itertools.groupby(self.get_objects(), get_group_func):
            orders = set()
            zero_price = total_charged = self.shop.create_price(0).amount

            # keep track the last one
            order_line = None

            for order_line in group:
                orders.add(order_line.order_id)
                total_charged += order_line.taxful_price.amount

            if total_charged > zero_price:
                data.append({
                    "carrier": order_line.order.shipping_method.carrier.name,
                    "shipping_method": order_line.order.shipping_method_name,
                    "order_count": len(orders),
                    "total_charged": total_charged.as_rounded().value
                })

        return self.get_return_data(data)
