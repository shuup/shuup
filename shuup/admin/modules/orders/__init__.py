# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from datetime import timedelta
from django.db.models import Q
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry, Notification, SearchResult
from shuup.admin.menu import ORDERS_MENU_CATEGORY, STOREFRONT_MENU_CATEGORY
from shuup.admin.shop_provider import get_shop
from shuup.admin.utils.urls import admin_url, derive_model_url, get_edit_and_list_urls, get_model_url
from shuup.admin.views.home import HelpBlockCategory, SimpleHelpBlock
from shuup.core.models import Order, OrderStatus, OrderStatusRole


class OrderEntry(MenuEntry):
    name = _("Orders")

    def get_badge(self, request):
        shop = get_shop(request)
        received_orders_count = (
            Order.objects.valid()
            .filter(
                shop=shop,
                status__role=OrderStatusRole.INITIAL,
            )
            .count()
        )

        if received_orders_count:
            return {"tag": "danger", "value": received_orders_count}


class OrderModule(AdminModule):
    name = _("Orders")
    breadcrumbs_menu_entry = OrderEntry(name, url="shuup_admin:order.list")

    def get_urls(self):
        return [
            admin_url(
                r"^orders/(?P<pk>\d+)/create-shipment/(?P<supplier_pk>\d+)/$",
                "shuup.admin.modules.orders.views.OrderCreateShipmentView",
                name="order.create-shipment",
            ),
            admin_url(
                r"^shipments/(?P<pk>\d+)/delete/$",
                "shuup.admin.modules.orders.views.ShipmentDeleteView",
                name="order.delete-shipment",
            ),
            admin_url(
                r"^shipments/(?P<pk>\d+)/set-sent/$",
                "shuup.admin.modules.orders.views.ShipmentSetSentView",
                name="order.set-shipment-sent",
            ),
            admin_url(
                r"^shipments/$", "shuup.admin.modules.orders.views.ShipmentListView", name="order.shipments.list"
            ),
            admin_url(
                r"^orders/(?P<pk>\d+)/create-payment/$",
                "shuup.admin.modules.orders.views.OrderCreatePaymentView",
                name="order.create-payment",
            ),
            admin_url(
                r"^orders/(?P<pk>\d+)/delete-payment/$",
                "shuup.admin.modules.orders.views.OrderDeletePaymentView",
                name="order.delete-payment",
            ),
            admin_url(
                r"^orders/(?P<pk>\d+)/set-paid/$",
                "shuup.admin.modules.orders.views.OrderSetPaidView",
                name="order.set-paid",
            ),
            admin_url(
                r"^orders/(?P<pk>\d+)/set-status/$",
                "shuup.admin.modules.orders.views.OrderSetStatusView",
                name="order.set-status",
            ),
            admin_url(
                r"^orders/(?P<pk>\d+)/new-log-entry/$",
                "shuup.admin.modules.orders.views.NewLogEntryView",
                name="order.new-log-entry",
            ),
            admin_url(
                r"^orders/(?P<pk>\d+)/update-admin-comment/$",
                "shuup.admin.modules.orders.views.UpdateAdminCommentView",
                name="order.update-admin-comment",
            ),
            admin_url(
                r"^orders/(?P<pk>\d+)/create-refund/$",
                "shuup.admin.modules.orders.views.OrderCreateRefundView",
                name="order.create-refund",
            ),
            admin_url(
                r"^orders/(?P<pk>\d+)/create-refund/full-refund$",
                "shuup.admin.modules.orders.views.OrderCreateFullRefundView",
                name="order.create-full-refund",
            ),
            admin_url(
                r"^orders/(?P<pk>\d+)/$", "shuup.admin.modules.orders.views.OrderDetailView", name="order.detail"
            ),
            admin_url(r"^orders/new/$", "shuup.admin.modules.orders.views.OrderEditView", name="order.new"),
            admin_url(
                r"^orders/(?P<pk>\d+)/edit/$", "shuup.admin.modules.orders.views.OrderEditView", name="order.edit"
            ),
            admin_url(r"^orders/$", "shuup.admin.modules.orders.views.OrderListView", name="order.list"),
            admin_url(
                r"^orders/list-settings/",
                "shuup.admin.modules.settings.views.ListSettingsView",
                name="order.list_settings",
            ),
            admin_url(
                r"^orders/(?P<pk>\d+)/edit-addresses/$",
                "shuup.admin.modules.orders.views.OrderAddressEditView",
                name="order.edit-addresses",
            ),
        ]

    def get_menu_entries(self, request):
        return [
            OrderEntry(
                text=_("Orders"),
                icon="fa fa-inbox",
                url="shuup_admin:order.list",
                category=ORDERS_MENU_CATEGORY,
                ordering=1,
                aliases=[_("Show orders")],
            ),
            MenuEntry(
                text=_("Shipments"),
                icon="fa fa-truck",
                url="shuup_admin:order.shipments.list",
                category=ORDERS_MENU_CATEGORY,
                ordering=2,
                aliases=[_("Show shipments")],
            ),
        ]

    def get_search_results(self, request, query):
        minimum_query_length = 3
        if len(query) >= minimum_query_length:
            orders = Order.objects.filter(
                Q(identifier__istartswith=query)
                | Q(reference_number__istartswith=query)
                | Q(email__icontains=query)
                | Q(phone__icontains=query)
            ).order_by("-id")[:15]

            for i, order in enumerate(orders):
                relevance = 100 - i
                yield SearchResult(
                    text=six.text_type(order), url=get_model_url(order), category=_("Orders"), relevance=relevance
                )

    def get_notifications(self, request):
        shop = request.shop
        old_open_orders = Order.objects.filter(
            shop=shop, status__role=OrderStatusRole.INITIAL, order_date__lt=now() - timedelta(days=4)
        ).count()

        if old_open_orders:
            yield Notification(
                title=_("Outstanding Orders"), text=_("%d outstanding orders") % old_open_orders, kind="danger"
            )

    def get_model_url(self, object, kind, shop=None):
        return derive_model_url(Order, "shuup_admin:order", object, kind)

    def get_help_blocks(self, request, kind):
        from shuup.admin.utils.permissions import has_permission

        if kind == "quicklink" and has_permission(request.user, "order.new"):
            actions = [{"text": _("New order"), "url": self.get_model_url(Order, "new")}]

            yield SimpleHelpBlock(
                text=_("New order"),
                actions=actions,
                icon_url="shuup_admin/img/product.png",
                priority=0,
                category=HelpBlockCategory.ORDERS,
                done=Order.objects.filter(shop=request.shop).exists() if kind == "setup" else False,
            )


class OrderStatusModule(AdminModule):
    name = _("Order Status")
    breadcrumbs_menu_entry = OrderEntry(name, url="shuup_admin:order_status.list")

    def get_urls(self):
        return get_edit_and_list_urls(
            url_prefix="^order-status",
            view_template="shuup.admin.modules.orders.views.OrderStatus%sView",
            name_template="order_status.%s",
        )

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Order Status"),
                icon="fa fa-inbox",
                url="shuup_admin:order_status.list",
                category=STOREFRONT_MENU_CATEGORY,
                ordering=1,
                aliases=[_("List Statuses")],
            ),
        ]

    def get_model_url(self, object, kind, shop=None):
        return derive_model_url(OrderStatus, "shuup_admin:order_status", object, kind)
