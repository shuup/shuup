# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from collections import OrderedDict
from datetime import date, timedelta
from decimal import Decimal

import six
from babel.dates import format_date
from dateutil import rrule
from django.db.models import Avg, Count, Sum
from django.utils.translation import ugettext_lazy as _

from shuup.admin.dashboard import (
    ChartDataType, ChartType, DashboardChartBlock, DashboardContentBlock,
    DashboardMoneyBlock, MixedChart
)
from shuup.core.models import Order
from shuup.core.pricing import TaxfulPrice
from shuup.core.utils.query import group_by_period
from shuup.utils.dates import get_year_and_month_format
from shuup.utils.i18n import get_current_babel_locale


def get_orders_for_request(request):
    shop = request.session.get("admin_shop")
    return Order.objects.filter(shop=shop, currency=shop.currency)


def month_iter(start_date, end_date):
    return ((d.month, d.year) for d in rrule.rrule(rrule.MONTHLY, dtstart=start_date, until=end_date))


class OrderValueChartDashboardBlock(DashboardChartBlock):
    default_size = "small"

    def __init__(self, id, request, **kwargs):
        self.cached_chart = None
        self.request = request
        self.currency = request.session.get("admin_shop").currency
        super(OrderValueChartDashboardBlock, self).__init__(id, **kwargs)

    @property
    def size(self):
        data_size = 0
        for dataset in self.get_chart().datasets:
            data_size = max(data_size, len(dataset["data"]))
        # the size will be dynamic. small for periods up to 4 months, otherwise medium
        return ("medium" if data_size > 4 else "small")

    @size.setter
    def size(self, value):
        # do not raise!
        pass

    def get_chart(self):
        if self.cached_chart is not None:
            return self.cached_chart

        chart_options = {
            "scales": {
                "yAxes": [{
                    "ticks": {
                        "beginAtZero": True
                    }
                }]
            }
        }

        today = date.today()
        chart_start_date = today - timedelta(days=365)

        orders = get_orders_for_request(self.request)
        sum_sales_data = group_by_period(
            orders.valid().since((today - chart_start_date).days),
            "order_date",
            "month",
            sum=Sum("taxful_total_price_value")
        )

        for (month, year) in month_iter(chart_start_date, today):
            sales_date = date(year, month, 1)
            if sales_date not in sum_sales_data:
                sum_sales_data[sales_date] = {"sum": Decimal(0)}

        # sort and recreated the ordered dict since we've put new items into
        sum_sales_data = OrderedDict(sorted(six.iteritems(sum_sales_data), key=lambda x: x[0]))

        locale = get_current_babel_locale()
        labels = [
            format_date(k, format=get_year_and_month_format(locale), locale=locale)
            for k in sum_sales_data
        ]
        mixed_chart = MixedChart(title=_("Sales per Month (past 12 months)"),
                                 labels=labels,
                                 data_type=ChartDataType.CURRENCY,
                                 options=chart_options,
                                 currency=self.currency,
                                 locale=locale)

        cumulative_sales = []
        average_sales = []

        # only calculate cumulative and average if there are at least 3 months
        if len(sum_sales_data) >= 3:
            count = 0
            total = Decimal()

            for month_sale in sum_sales_data.values():
                total = total + month_sale["sum"]
                cumulative_sales.append(total)
                average_sales.append(total / (count+1))
                count = count + 1

        # this will be on top of all bars
        if average_sales:
            mixed_chart.add_data(_("Average Sales"), [v for v in average_sales], ChartType.LINE)

        # this will be under the cummulative bars
        mixed_chart.add_data(_("Sales"), [v["sum"] for v in sum_sales_data.values()], ChartType.BAR)

        # this will be under all others charts
        if cumulative_sales:
            mixed_chart.add_data(_("Cumulative Total Sales"), [v for v in cumulative_sales], ChartType.BAR)

        self.cached_chart = mixed_chart
        return mixed_chart


def get_subtitle(count):
    return _("Based on %d orders") % count


def get_sales_of_the_day_block(request):
    orders = get_orders_for_request(request)
    # Sales of the day
    todays_order_data = (
        orders.complete().since(0)
        .aggregate(count=Count("id"), sum=Sum("taxful_total_price_value")))

    return DashboardMoneyBlock(
        id="todays_order_sum",
        color="green",
        title=_("Today's Sales"),
        value=(todays_order_data.get("sum") or 0),
        currency=request.session.get("admin_shop").currency,
        icon="fa fa-calculator",
        subtitle=get_subtitle(todays_order_data.get("count"))
    )


def get_lifetime_sales_block(request):
    orders = get_orders_for_request(request)

    # Lifetime sales
    lifetime_sales_data = orders.complete().aggregate(
        count=Count("id"),
        sum=Sum("taxful_total_price_value")
    )

    return DashboardMoneyBlock(
        id="lifetime_sales_sum",
        color="green",
        title=_("Lifetime Sales"),
        value=(lifetime_sales_data.get("sum") or 0),
        currency=request.session.get("admin_shop").currency,
        icon="fa fa-line-chart",
        subtitle=get_subtitle(lifetime_sales_data.get("count"))
    )


def get_avg_purchase_size_block(request):
    orders = get_orders_for_request(request)

    lifetime_sales_data = orders.complete().aggregate(
        count=Count("id"),
        sum=Sum("taxful_total_price_value")
    )

    # Average size of purchase with amount of orders it is calculated from
    average_purchase_size = (
        Order.objects.filter(shop=request.session.get("admin_shop"))
        .aggregate(count=Count("id"), sum=Avg("taxful_total_price_value")))
    return DashboardMoneyBlock(
        id="average_purchase_sum",
        color="blue",
        title=_("Average Purchase"),
        value=(average_purchase_size.get("sum") or 0),
        currency=request.session.get("admin_shop").currency,
        icon="fa fa-shopping-cart",
        subtitle=get_subtitle(lifetime_sales_data.get("count"))
    )


def get_open_orders_block(request):
    orders = get_orders_for_request(request)

    # Open orders / open orders value
    open_order_data = (
        orders.incomplete()
        .aggregate(count=Count("id"), sum=Sum("taxful_total_price_value")))

    currency = request.session.get("admin_shop").currency
    return DashboardMoneyBlock(
        id="open_orders_sum",
        color="orange",
        title=_("Open Orders Value"),
        value=TaxfulPrice((open_order_data.get("sum") or 0), currency),
        currency=currency,
        icon="fa fa-inbox",
        subtitle=get_subtitle(open_order_data.get("count"))
    )


def get_order_value_chart_dashboard_block(request):
    return OrderValueChartDashboardBlock(id="order_value_chart", request=request)


def get_order_overview_for_date_range(request, start_date, end_date):
    orders = get_orders_for_request(request).complete()
    q = orders.since((end_date - start_date).days).aggregate(
        num_orders=Count("id"),
        num_customers=Count("customer", distinct=True),
        sales=Sum("taxful_total_price_value"))
    anon_orders = orders.since((end_date - start_date).days).filter(customer__isnull=True).aggregate(
        num_orders=Count("id"))
    q["num_customers"] += anon_orders["num_orders"]
    q["sales"] = TaxfulPrice(q["sales"] or 0, request.session.get("admin_shop").currency)
    return q


def get_shop_overview_block(request):
    today = date.today()
    start_of_month = date(today.year, today.month, 1)
    start_of_year = date(today.year, 1, 1)
    daily = get_order_overview_for_date_range(request, today, today)
    mtd = get_order_overview_for_date_range(request, start_of_month, today)
    ytd = get_order_overview_for_date_range(request, start_of_year, today)
    totals = get_orders_for_request(request).complete().aggregate(
        num_orders=Count("id"),
        num_customers=Count("customer", distinct=True),
        sales=Sum("taxful_total_price_value")
    )
    anon_orders = get_orders_for_request(request).complete().filter(customer__isnull=True).aggregate(
        num_orders=Count("id"))
    totals["num_customers"] += anon_orders["num_orders"]
    totals["sales"] = TaxfulPrice(totals["sales"] or 0, request.session.get("admin_shop").currency)
    block = DashboardContentBlock.by_rendering_template(
        "store_overview", request, "shuup/admin/sales_dashboard/_store_overview_dashboard_block.jinja", {
            "daily": daily,
            "mtd": mtd,
            "ytd": ytd,
            "totals": totals
        })
    block.size = "small"
    return block


def get_recent_orders_block(request):
    orders = get_orders_for_request(request).valid().order_by("-order_date")[:5]
    block = DashboardContentBlock.by_rendering_template(
        "recent_orders", request, "shuup/admin/sales_dashboard/_recent_orders_dashboard_block.jinja", {
            "orders": orders
        }
    )
    block.size = "small"
    return block
