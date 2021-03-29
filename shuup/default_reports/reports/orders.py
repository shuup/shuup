# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import OrderLineType
from shuup.default_reports.forms import OrderLineReportForm, OrderReportForm
from shuup.default_reports.mixins import OrderLineReportMixin, OrderReportMixin
from shuup.reports.report import ShuupReportBase
from shuup.utils.i18n import format_money, get_locally_formatted_datetime


class OrdersReport(OrderReportMixin, ShuupReportBase):
    identifier = "orders_report"
    title = _("Orders Report")
    form_class = OrderReportForm

    filename_template = "orders-report-%(time)s"
    schema = [
        {"key": "order_num", "title": _("Order ref.")},
        {"key": "order_date", "title": _("Order date")},
        {"key": "customer", "title": _("Customer")},
        {"key": "status", "title": _("Status")},
        {"key": "order_line_quantity", "title": _("Order line quantity")},
        {"key": "payment_status", "title": _("Payment status")},
        {"key": "shipment_status", "title": _("Shipment status")},
        {"key": "order_total_amount", "title": _("Total")},
    ]

    def get_data(self):
        data = []
        orders = self.get_objects(paid=False)

        for order in orders:
            data.append(
                {
                    "order_num": order.identifier,
                    "order_date": get_locally_formatted_datetime(order.order_date),
                    "status": order.status,
                    "order_line_quantity": order.lines.filter(type=OrderLineType.PRODUCT).count(),
                    "order_total_amount": format_money(order.taxful_total_price),
                    "payment_status": order.get_payment_status_display(),
                    "shipment_status": order.get_shipping_status_display(),
                    "customer": order.get_customer_name(),
                }
            )
        return self.get_return_data(data, has_totals=False)


class OrderLineReport(OrderLineReportMixin, ShuupReportBase):
    identifier = "order_line_report"
    title = _("Order Line Report")
    form_class = OrderLineReportForm

    filename_template = "orders-report-%(time)s"
    schema = [
        {"key": "order_line_sku", "title": _("Order Line SKU")},
        {"key": "order_line_text", "title": _("Order Line Text")},
        {"key": "order_line_quantity", "title": _("Quantity")},
        {"key": "taxless_unit_price", "title": _("Taxless Unit Price")},
        {"key": "taxful_unit_price", "title": _("Taxful Unit Price")},
        {"key": "taxful_price", "title": _("Taxful Price")},
        {"key": "created_on", "title": _("Created on")},
        {"key": "type", "title": _("Type")},
    ]

    def get_data(self):
        data = []
        order_lines = self.get_objects()[: self.queryset_row_limit]
        for line in order_lines:
            data.append(
                {
                    "order_line_sku": line.sku,
                    "order_line_text": line.text,
                    "order_line_quantity": line.quantity,
                    "taxless_unit_price": format_money(line.taxless_base_unit_price),
                    "taxful_unit_price": format_money(line.taxful_base_unit_price),
                    "taxful_price": format_money(line.taxful_price),
                    "type": line.type.name.capitalize(),
                    "created_on": get_locally_formatted_datetime(line.created_on),
                }
            )
        return self.get_return_data(data, has_totals=False)
