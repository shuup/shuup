# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from babel.dates import format_date
from django.conf import settings
from django.db.models import Count, Avg, Sum
from django.utils.translation import ugettext_lazy as _
from shoop.admin.dashboard import DashboardMoneyBlock, DashboardChartBlock, BarChart
from shoop.core.models import Order
from shoop.core.utils.query import group_by_period
from shoop.utils.dates import get_year_and_month_format
from shoop.utils.i18n import get_current_babel_locale
from shoop.utils.numbers import bankers_round


class OrderValueChartDashboardBlock(DashboardChartBlock):
    def get_chart(self):
        aggregate_data = group_by_period(
            Order.objects.valid().since(days=365),
            "order_date",
            "month",
            sum=Sum("taxful_total_price")
        )
        locale = get_current_babel_locale()
        bar_chart = BarChart(title=_("Sales per Month (last year)"), labels=[
            format_date(k, format=get_year_and_month_format(locale), locale=locale)
            for k in aggregate_data
        ])
        bar_chart.add_data(
            _("Sales (%(currency)s)") % {"currency": settings.SHOOP_HOME_CURRENCY},
            [bankers_round(v["sum"], settings.SHOOP_ORDER_TOTAL_DECIMALS) for v in aggregate_data.values()]
        )
        return bar_chart


def get_subtitle(count):
    return _("Based on %d orders") % count


def get_sales_of_the_day_block(request):
    # Sales of the day
    todays_order_data = Order.objects.complete().since(0).aggregate(count=Count("id"), sum=Sum("taxful_total_price"))

    return DashboardMoneyBlock(
        id="todays_order_sum",
        color="green",
        title=_("Today's Sales"),
        value=(todays_order_data.get("sum") or 0),
        icon="fa fa-calculator",
        subtitle=get_subtitle(todays_order_data.get("count"))
    )


def get_lifetime_sales_block(request):
    # Lifetime sales
    lifetime_sales_data = Order.objects.complete().aggregate(
        count=Count("id"),
        sum=Sum("taxful_total_price")
    )

    return DashboardMoneyBlock(
        id="lifetime_sales_sum",
        color="green",
        title=_("Lifetime Sales"),
        value=(lifetime_sales_data.get("sum") or 0),
        icon="fa fa-line-chart",
        subtitle=get_subtitle(lifetime_sales_data.get("count"))
    )


def get_avg_purchase_size_block(request):
    lifetime_sales_data = Order.objects.complete().aggregate(
        count=Count("id"),
        sum=Sum("taxful_total_price")
    )

    # Average size of purchase with amount of orders it is calculated from
    average_purchase_size = Order.objects.all().aggregate(count=Count("id"), sum=Avg("taxful_total_price"))
    return DashboardMoneyBlock(
        id="average_purchase_sum",
        color="blue",
        title=_("Average Purchase"),
        value=(average_purchase_size.get("sum") or 0),
        icon="fa fa-shopping-cart",
        subtitle=get_subtitle(lifetime_sales_data.get("count"))
    )


def get_open_orders_block(request):
    # Open orders / open orders value
    open_order_data = Order.objects.incomplete().aggregate(count=Count("id"), sum=Sum("taxful_total_price"))

    return DashboardMoneyBlock(
        id="open_orders_sum",
        color="orange",
        title=_("Open Orders Value"),
        value=(open_order_data.get("sum") or 0),
        icon="fa fa-inbox",
        subtitle=get_subtitle(open_order_data.get("count"))
    )


def get_order_value_chart_dashboard_block(request):
    return OrderValueChartDashboardBlock(id="order_value_chart")
