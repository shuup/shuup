# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
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
from shoop.admin.utils.permissions import (
    get_default_model_permissions, get_permissions_from_urls
)
from shoop.admin.utils.urls import admin_url, derive_model_url, get_model_url
from shoop.core.models import (
    Contact, Order, OrderStatusRole, Product, PurchaseOrder
)


class OrderModule(CurrencyBound, AdminModule):
    name = _("Orders")

    def get_urls(self):
        return [
            admin_url(
                "^orders/(?P<pk>\d+)/create-shipment/$",
                "shoop.admin.modules.orders.views.OrderCreateShipmentView",
                name="order.create-shipment",
                permissions=["shoop.add_shipment"]
            ),
            admin_url(
                "^orders/(?P<pk>\d+)/create-payment/$",
                "shoop.admin.modules.orders.views.OrderCreatePaymentView",
                name="order.create-payment",
                permissions=["shoop.add_payment"]
            ),
            admin_url(
                "^orders/(?P<pk>\d+)/set-status/$",
                "shoop.admin.modules.orders.views.OrderSetStatusView",
                name="order.set-status",
                permissions=get_default_model_permissions(Order)
            ),
            admin_url(
                "^orders/(?P<pk>\d+)/new-log-entry/$",
                "shoop.admin.modules.orders.views.NewLogEntryView",
                name="order.new-log-entry",
                permissions=get_default_model_permissions(Order)
            ),
            admin_url(
                "^orders/(?P<pk>\d+)/create-refund/$",
                "shoop.admin.modules.orders.views.OrderCreateRefundView",
                name="order.create-refund",
                permissions=get_default_model_permissions(Order)
            ),
            admin_url(
                "^orders/(?P<pk>\d+)/create-refund/full-refund$",
                "shoop.admin.modules.orders.views.OrderCreateFullRefundView",
                name="order.create-full-refund",
                permissions=get_default_model_permissions(Order)
            ),
            admin_url(
                "^orders/(?P<pk>\d+)/$",
                "shoop.admin.modules.orders.views.OrderDetailView",
                name="order.detail",
                permissions=get_default_model_permissions(Order)
            ),
            admin_url(
                "^orders/new/$",
                "shoop.admin.modules.orders.views.OrderEditView",
                name="order.new",
                permissions=["shoop.add_order"]
            ),
            admin_url(
                "^orders/(?P<pk>\d+)/edit/$",
                "shoop.admin.modules.orders.views.OrderEditView",
                name="order.edit",
                permissions=["shoop.change_order"]
            ),
            admin_url(
                "^orders/$",
                "shoop.admin.modules.orders.views.OrderListView",
                name="order.list",
                permissions=get_default_model_permissions(Order),

            ),
            admin_url(
                "^purchase-orders/(?P<pk>\d+)/$",
                "shoop.admin.modules.orders.views.PurchaseOrderDetailView",
                name="purchase_order.detail"
            ),
            admin_url(
                "^purchase-orders/new/$",
                "shoop.admin.modules.orders.views.PurchaseOrderEditView",
                name="purchase_order.new"
            ),
            admin_url(
                "^purchase-orders/$",
                "shoop.admin.modules.orders.views.PurchaseOrderListView",
                name="purchase_order.list"
            ),
        ]

    def get_menu_category_icons(self):
        return {self.name: "fa fa-inbox"}

    def get_menu_entries(self, request):
        category = _("Orders")
        return [
            MenuEntry(
                text=_("Sales Orders"),
                icon="fa fa-inbox",
                url="shoop_admin:order.list",
                category=category,
                aliases=[_("Show sales orders")]
            ),
            MenuEntry(
                text=_("Purchase Orders"),
                icon="fa fa-inbox",
                url="shoop_admin:purchase_order.list",
                category=category,
                aliases=[_("Show purchase orders")]
            ),
        ]

    def get_required_permissions(self):
        return (
            get_permissions_from_urls(self.get_urls()) |
            get_default_model_permissions(Contact) |
            get_default_model_permissions(Order) |
            get_default_model_permissions(Product)
        )

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
        return (
            derive_model_url(PurchaseOrder, "shoop_admin:purchase_order", object, kind) or
            derive_model_url(Order, "shoop_admin:order", object, kind)
        )
