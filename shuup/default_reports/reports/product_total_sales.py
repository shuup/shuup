# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import itertools
from django.utils.translation import ugettext_lazy as _
from operator import itemgetter

from shuup.core.models import OrderLine
from shuup.core.pricing import TaxfulPrice, TaxlessPrice
from shuup.default_reports.forms import ProductTotalSalesReportForm
from shuup.default_reports.mixins import OrderReportMixin
from shuup.reports.report import ShuupReportBase


class ProductSalesReport(OrderReportMixin, ShuupReportBase):
    identifier = "product_total_sales_report"
    title = _("Product Total Sales")
    form_class = ProductTotalSalesReportForm

    filename_template = "product-total-sales-report-%(time)s"
    schema = [
        {"key": "product", "title": _("Product")},
        {"key": "sku", "title": _("SKU")},
        {"key": "quantity", "title": _("Quantity")},
        {"key": "taxless_total", "title": _("Taxless Total")},
        {"key": "taxful_total", "title": _("Taxful Total")},
    ]

    def get_objects(self):
        order_line_qs = OrderLine.objects.products().filter(order__in=super(ProductSalesReport, self).get_objects())
        return (
            order_line_qs.select_related("product")
            .prefetch_related("taxes")
            .order_by("product__id")[: self.queryset_row_limit]
        )

    def get_data(self):
        data = []

        # group products by id - que queryset must be ordered by id to make this work
        for key, groups in itertools.groupby(self.get_objects(), lambda pl: pl.product_id):
            quantity = 0
            taxful_total = TaxfulPrice(0, self.shop.currency)
            taxless_total = TaxlessPrice(0, self.shop.currency)
            product = None

            for order_line in groups:
                quantity += order_line.quantity
                taxful_total += order_line.taxful_price
                taxless_total += order_line.taxless_price

                if not product:
                    product = order_line.product

            data.append(
                {
                    "product": product.name,
                    "sku": product.sku,
                    "quantity": quantity,
                    "taxful_total": taxful_total.as_rounded().value,
                    "taxless_total": taxless_total.as_rounded().value,
                }
            )

        order_by = self.options.get("order_by")
        if order_by:
            data = sorted(data, key=itemgetter(order_by), reverse=True)

        return self.get_return_data(data)
