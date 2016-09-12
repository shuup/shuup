# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from babel.dates import format_date
from django.db.models import Avg, Count, Sum
from django.utils.translation import ugettext_lazy as _

from shuup.admin.dashboard import (
    BarChart, DashboardChartBlock, DashboardMoneyBlock
)
from shuup.core.models import Order
from shuup.core.pricing import TaxfulPrice
from shuup.core.utils.query import group_by_period
from shuup.utils.dates import get_year_and_month_format
from shuup.utils.i18n import get_current_babel_locale


def get_orders_by_currency(currency):
    return Order.objects.filter(currency=currency)


class OrderValueChartDashboardBlock(DashboardChartBlock):
    def __init__(self, id, currency, **kwargs):
        self.currency = currency
        super(OrderValueChartDashboardBlock, self).__init__(id, **kwargs)

    def get_chart(self):
        orders = get_orders_by_currency(self.currency)
        aggregate_data = group_by_period(
            orders.valid().since(days=365),
            "order_date",
            "month",
            sum=Sum("taxful_total_price_value")
        )
        locale = get_current_babel_locale()
        bar_chart = BarChart(title=_("Sales per Month (last year)"), labels=[
            format_date(k, format=get_year_and_month_format(locale), locale=locale)
            for k in aggregate_data
        ])
        bar_chart.add_data(
            _("Sales (%(currency)s)") % {"currency": self.currency},
            [v["sum"] for v in aggregate_data.values()]
        )
        return bar_chart


def get_subtitle(count):
    return _("Based on %d orders") % count


def get_sales_of_the_day_block(request, currency):
    orders = get_orders_by_currency(currency)
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


def get_lifetime_sales_block(request, currency):
    orders = get_orders_by_currency(currency)

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
        subtitle=get_subtitle(lifetime_sales_data.get("count"))
    )


def get_avg_purchase_size_block(request, currency):
    orders = get_orders_by_currency(currency)

    lifetime_sales_data = orders.complete().aggregate(
        count=Count("id"),
        sum=Sum("taxful_total_price_value")
    )

    # Average size of purchase with amount of orders it is calculated from
    average_purchase_size = (
        Order.objects.all()
        .aggregate(count=Count("id"), sum=Avg("taxful_total_price_value")))
    return DashboardMoneyBlock(
        id="average_purchase_sum",
        color="blue",
        title=_("Average Purchase"),
        value=(average_purchase_size.get("sum") or 0),
        currency=currency,
        icon="fa fa-shopping-cart",
        subtitle=get_subtitle(lifetime_sales_data.get("count"))
    )


def get_open_orders_block(request, currency):
    orders = get_orders_by_currency(currency)

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
        subtitle=get_subtitle(open_order_data.get("count"))
    )


def get_order_value_chart_dashboard_block(request, currency):
    return OrderValueChartDashboardBlock(id="order_value_chart", currency=currency)
