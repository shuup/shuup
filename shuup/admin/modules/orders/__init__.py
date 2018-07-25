# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from datetime import timedelta

import six
from django.db.models import Q
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule, MenuEntry, Notification, SearchResult
from shuup.admin.menu import ORDERS_MENU_CATEGORY, STOREFRONT_MENU_CATEGORY
from shuup.admin.utils.permissions import (
    get_default_model_permissions, get_permissions_from_urls
)
from shuup.admin.utils.urls import (
    admin_url, derive_model_url, get_edit_and_list_urls, get_model_url
)
from shuup.admin.views.home import HelpBlockCategory, SimpleHelpBlock
from shuup.core.models import (
    Contact, Order, OrderStatus, OrderStatusRole, Product
)


class OrderModule(AdminModule):
    name = _("Orders")
    breadcrumbs_menu_entry = MenuEntry(name, url="shuup_admin:order.list")

    def get_urls(self):
        return [
            admin_url(
                "^orders/(?P<pk>\d+)/create-shipment/$",
                "shuup.admin.modules.orders.views.OrderCreateShipmentView",
                name="order.create-shipment",
                permissions=["shuup.add_shipment"]
            ),
            admin_url(
                "^shipments/(?P<pk>\d+)/delete/$",
                "shuup.admin.modules.orders.views.ShipmentDeleteView",
                name="order.delete-shipment",
                permissions=["shuup.delete_shipment"]
            ),
            admin_url(
                "^orders/(?P<pk>\d+)/create-payment/$",
                "shuup.admin.modules.orders.views.OrderCreatePaymentView",
                name="order.create-payment",
                permissions=["shuup.add_payment"]
            ),
            admin_url(
                "^orders/(?P<pk>\d+)/set-paid/$",
                "shuup.admin.modules.orders.views.OrderSetPaidView",
                name="order.set-paid",
                permissions=["shuup.add_payment"]
            ),
            admin_url(
                "^orders/(?P<pk>\d+)/set-status/$",
                "shuup.admin.modules.orders.views.OrderSetStatusView",
                name="order.set-status",
                permissions=get_default_model_permissions(Order)
            ),
            admin_url(
                "^orders/(?P<pk>\d+)/new-log-entry/$",
                "shuup.admin.modules.orders.views.NewLogEntryView",
                name="order.new-log-entry",
                permissions=get_default_model_permissions(Order)
            ),
            admin_url(
                "^orders/(?P<pk>\d+)/update-admin-comment/$",
                "shuup.admin.modules.orders.views.UpdateAdminCommentView",
                name="order.update-admin-comment",
                permissions=get_default_model_permissions(Order)
            ),
            admin_url(
                "^orders/(?P<pk>\d+)/create-refund/$",
                "shuup.admin.modules.orders.views.OrderCreateRefundView",
                name="order.create-refund",
                permissions=get_default_model_permissions(Order)
            ),
            admin_url(
                "^orders/(?P<pk>\d+)/create-refund/full-refund$",
                "shuup.admin.modules.orders.views.OrderCreateFullRefundView",
                name="order.create-full-refund",
                permissions=get_default_model_permissions(Order)
            ),
            admin_url(
                "^orders/(?P<pk>\d+)/$",
                "shuup.admin.modules.orders.views.OrderDetailView",
                name="order.detail",
                permissions=get_default_model_permissions(Order)
            ),
            admin_url(
                "^orders/new/$",
                "shuup.admin.modules.orders.views.OrderEditView",
                name="order.new",
                permissions=["shuup.add_order"]
            ),
            admin_url(
                "^orders/(?P<pk>\d+)/edit/$",
                "shuup.admin.modules.orders.views.OrderEditView",
                name="order.edit",
                permissions=["shuup.change_order"]
            ),
            admin_url(
                "^orders/$",
                "shuup.admin.modules.orders.views.OrderListView",
                name="order.list",
                permissions=get_default_model_permissions(Order),

            ),
            admin_url(
                "^orders/list-settings/",
                "shuup.admin.modules.settings.views.ListSettingsView",
                name="order.list_settings",
                permissions=get_default_model_permissions(Order),
            ),
            admin_url(
                "^orders/(?P<pk>\d+)/edit-addresses/$",
                "shuup.admin.modules.orders.views.OrderAddressEditView",
                name="order.edit-addresses",
                permissions=["shuup.change_order"]
            ),
        ] + get_edit_and_list_urls(
            url_prefix="^order-status",
            view_template="shuup.admin.modules.orders.views.OrderStatus%sView",
            name_template="order_status.%s",
            permissions=get_default_model_permissions(OrderStatus)
        )

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=_("Orders"),
                icon="fa fa-inbox",
                url="shuup_admin:order.list",
                category=ORDERS_MENU_CATEGORY,
                subcategory="orders",
                ordering=1,
                aliases=[_("Show orders")]
            ),
            MenuEntry(
                text=_("Order Status"),
                icon="fa fa-inbox",
                url="shuup_admin:order_status.list",
                category=STOREFRONT_MENU_CATEGORY,
                subcategory="settings",
                ordering=1,
                aliases=[_("List Statuses")]
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
        if len(query) >= self.minimum_search_length:
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

    def get_notifications(self, request):
        shop = request.shop
        old_open_orders = Order.objects.filter(
            shop=shop,
            status__role=OrderStatusRole.INITIAL,
            order_date__lt=now() - timedelta(days=4)
        ).count()

        if old_open_orders:
            yield Notification(
                title=_("Outstanding Orders"),
                text=_("%d outstanding orders") % old_open_orders,
                kind="danger"
            )

    def get_model_url(self, object, kind, shop=None):
        if hasattr(object, "role"):
            return derive_model_url(OrderStatus, "shuup_admin:order_status", object, kind)
        return derive_model_url(Order, "shuup_admin:order", object, kind)

    def get_help_blocks(self, request, kind):
        if kind == "quicklink":
            actions = [{
                "text": _("New order"),
                "url": self.get_model_url(Order, "new")
            }]

            yield SimpleHelpBlock(
                text=_("New order"),
                actions=actions,
                icon_url="shuup_admin/img/product.png",
                priority=0,
                category=HelpBlockCategory.ORDERS,
                done=Order.objects.filter(shop=request.shop).exists() if kind == "setup" else False
            )
