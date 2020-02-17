# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from collections import OrderedDict
from datetime import date, time, timedelta
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
from shuup.core.models import Order, Shop
from shuup.core.pricing import TaxfulPrice
from shuup.core.utils.query import group_by_period
from shuup.utils.dates import get_year_and_month_format, local_now, to_aware
from shuup.utils.i18n import get_current_babel_locale


def get_orders_for_shop(request, currency=None):
    shop = request.shop
    if not currency:
        currency = shop.currency
    return Order.objects.filter(shop=shop, currency=currency)


def get_orders_by_currency(currency):
    return Order.objects.filter(currency=currency)


def month_iter(start_date, end_date):
    return ((d.month, d.year) for d in rrule.rrule(rrule.MONTHLY, dtstart=start_date, until=end_date))


class OrderValueChartDashboardBlock(DashboardChartBlock):
    default_size = "small"

    def __init__(self, id, request, **kwargs):
        shop = request.shop
        self.cached_chart = None
        self.request = request
        self.currency = shop.currency
        super(OrderValueChartDashboardBlock, self).__init__(id, **kwargs)
        self.sort_order = 2

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

        orders = get_orders_for_shop(self.request)
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


def get_sales_of_the_day_block(request, currency=None):
    orders = get_orders_for_shop(request)
    if not currency:
        shop = request.shop
        currency = shop.currency

    # Sales of the day
    todays_order_data = (
        orders.complete().since(0)
        .aggregate(count=Count("id"), sum=Sum("taxful_total_price_value")))
    return DashboardMoneyBlock(
        id="todays_order_sum",
        color="green",
        title=_("Today's Sales"),
        value=(todays_order_data.get("sum") or 0),
        currency=currency,
        icon="fa fa-calculator",
        subtitle=get_subtitle(todays_order_data.get("count"))
    )


def get_lifetime_sales_block(request, currency=None):
    orders = get_orders_for_shop(request)
    if not currency:
        shop = request.shop
        currency = shop.currency

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
        currency=currency,
        icon="fa fa-line-chart",
        subtitle=get_subtitle(lifetime_sales_data.get("count")),
        sort_order=1
    )


def get_avg_purchase_size_block(request, currency=None):
    orders = get_orders_for_shop(request)
    shop = request.shop
    if not currency:
        currency = shop.currency

    lifetime_sales_data = orders.complete().aggregate(
        count=Count("id"),
        sum=Sum("taxful_total_price_value")
    )

    # Average size of purchase with amount of orders it is calculated from
    average_purchase_size = (
        Order.objects.filter(shop=shop)
        .aggregate(count=Count("id"), sum=Avg("taxful_total_price_value")))
    return DashboardMoneyBlock(
        id="average_purchase_sum",
        color="blue",
        title=_("Average Purchase"),
        value=(average_purchase_size.get("sum") or 0),
        currency=currency,
        icon="fa fa-shopping-cart",
        subtitle=get_subtitle(lifetime_sales_data.get("count")),
        sort_order=1
    )


def get_open_orders_block(request, currency=None):
    orders = get_orders_for_shop(request)
    if not currency:
        shop = request.shop
        currency = shop.currency

    # Open orders / open orders value
    open_order_data = (
        orders.incomplete()
        .aggregate(count=Count("id"), sum=Sum("taxful_total_price_value")))

    return DashboardMoneyBlock(
        id="open_orders_sum",
        color="orange",
        title=_("Open Orders Value"),
        value=TaxfulPrice((open_order_data.get("sum") or 0), currency),
        currency=currency,
        icon="fa fa-inbox",
        subtitle=get_subtitle(open_order_data.get("count")),
        sort_order=1
    )


def get_order_value_chart_dashboard_block(request, currency):
    return OrderValueChartDashboardBlock(id="order_value_chart", request=request)


def get_order_overview_for_date_range(currency, start_date, end_date, shop=None):
    if not shop:
        shop = Shop.objects.first()
    orders = get_orders_by_currency(currency).filter(shop=shop).complete()

    orders_in_range = orders.in_date_range(start_date, end_date)
    q = orders_in_range.aggregate(
        num_orders=Count("id"),
        num_customers=Count("customer", distinct=True),
        sales=Sum("taxful_total_price_value"))
    anon_orders = orders_in_range.filter(customer__isnull=True).aggregate(
        num_orders=Count("id"))
    q["num_customers"] += anon_orders["num_orders"]
    q["sales"] = TaxfulPrice(q["sales"] or 0, currency)
    return q


def get_shop_overview_block(request, currency, for_date=None):
    end = to_aware(for_date, time=time.max) if for_date else local_now()
    start_of_day = to_aware(end.date(), time=time.min)
    start_of_month = start_of_day.replace(day=1)
    start_of_year = start_of_day.replace(month=1, day=1)
    shop = request.shop

    if not currency:
        currency = shop.currency

    daily = get_order_overview_for_date_range(currency, start_of_day, end, shop=shop)
    mtd = get_order_overview_for_date_range(currency, start_of_month, end, shop=shop)
    ytd = get_order_overview_for_date_range(currency, start_of_year, end, shop=shop)
    totals = get_orders_by_currency(currency).complete().filter(shop=shop).aggregate(
        num_orders=Count("id"),
        num_customers=Count("customer", distinct=True),
        sales=Sum("taxful_total_price_value")
    )
    anon_orders = get_orders_by_currency(currency).complete().filter(customer__isnull=True, shop=shop).aggregate(
        num_orders=Count("id"))
    totals["num_customers"] += anon_orders["num_orders"]
    totals["sales"] = TaxfulPrice(totals["sales"] or 0, currency)
    block = DashboardContentBlock.by_rendering_template(
        "store_overview", request, "shuup/admin/sales_dashboard/_store_overview_dashboard_block.jinja", {
            "daily": daily,
            "mtd": mtd,
            "ytd": ytd,
            "totals": totals
        })
    block.size = "medium"
    block.sort_order = 0
    return block


def get_recent_orders_block(request, currency=None):
    orders = get_orders_for_shop(request).valid().order_by("-order_date")[:5]

    block = DashboardContentBlock.by_rendering_template(
        "recent_orders", request, "shuup/admin/sales_dashboard/_recent_orders_dashboard_block.jinja", {
            "orders": orders
        }
    )
    block.size = "medium"
    block.sort_order = 2
    return block
