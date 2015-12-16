# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from datetime import timedelta

import six
from django.db.models import Q
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from shoop.admin.base import AdminModule, MenuEntry, Notification, SearchResult
from shoop.admin.currencybound import CurrencyBound
from shoop.admin.utils.urls import admin_url, derive_model_url, get_model_url
from shoop.core.models import Order, OrderStatusRole


class OrderModule(CurrencyBound, AdminModule):
    name = _("Orders")
    breadcrumbs_menu_entry = MenuEntry(name, url="shoop_admin:order.list")

    def get_urls(self):
        return [
            admin_url(
                "^orders/(?P<pk>\d+)/create-shipment/$",
                "shoop.admin.modules.orders.views.OrderCreateShipmentView",
                name="order.create-shipment"
            ),
            admin_url(
                "^orders/(?P<pk>\d+)/set-status/$",
                "shoop.admin.modules.orders.views.OrderSetStatusView",
                name="order.set-status"
            ),
            admin_url(
                "^orders/(?P<pk>\d+)/$",
                "shoop.admin.modules.orders.views.OrderDetailView",
                name="order.detail"
            ),
            admin_url(
                "^orders/new/$",
                "shoop.admin.modules.orders.views.OrderCreateView",
                name="order.new"
            ),
            admin_url(
                "^orders/$",
                "shoop.admin.modules.orders.views.OrderListView",
                name="order.list"
            ),
        ]

    def get_menu_category_icons(self):
        return {self.name: "fa fa-inbox"}

    def get_menu_entries(self, request):
        category = _("Orders")
        return [
            MenuEntry(
                text=_("Orders"),
                icon="fa fa-inbox",
                url="shoop_admin:order.list",
                category=category,
                aliases=[_("Show orders")]
            ),
        ]

    def get_search_results(self, request, query):
        minimum_query_length = 3
        if len(query) >= minimum_query_length:
            orders = Order.objects.filter(
                Q(identifier__istartswith=query) |
                Q(reference_number__istartswith=query) |
                Q(email__icontains=query) |
                Q(phone__icontains=query)
            ).order_by("-id")[:15]

            for i, order in enumerate(orders):
                relevance = 100 - i
                yield SearchResult(
                    text=six.text_type(order),
                    url=get_model_url(order),
                    category=_("Orders"),
                    relevance=relevance
                )

    def get_dashboard_blocks(self, request):
        import shoop.admin.modules.orders.dashboard as dashboard
        currency = self.currency
        if not currency:
            return
        yield dashboard.get_sales_of_the_day_block(request, currency)
        yield dashboard.get_lifetime_sales_block(request, currency)
        yield dashboard.get_avg_purchase_size_block(request, currency)
        yield dashboard.get_open_orders_block(request, currency)
        yield dashboard.get_order_value_chart_dashboard_block(request, currency)

    def get_notifications(self, request):
        old_open_orders = Order.objects.filter(
            status__role=OrderStatusRole.INITIAL,
            order_date__lt=now() - timedelta(days=4)
        ).count()

        if old_open_orders:
            yield Notification(
                title=_("Outstanding Orders"),
                text=_("%d outstanding orders") % old_open_orders,
                kind="danger"
            )

    def get_model_url(self, object, kind):
        return derive_model_url(Order, "shoop_admin:order", object, kind)
