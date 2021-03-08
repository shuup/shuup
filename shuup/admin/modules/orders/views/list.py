# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _

from shuup.admin.shop_provider import get_shop
from shuup.admin.toolbar import NewActionButton, SettingsActionButton, Toolbar
from shuup.admin.utils.picotable import (
    ChoicesFilter, Column, DateRangeFilter, MultiFieldTextFilter, RangeFilter,
    TextFilter
)
from shuup.admin.utils.views import PicotableListView
from shuup.core.models import Order, OrderStatus, PaymentStatus, ShippingStatus
from shuup.utils.django_compat import reverse
from shuup.utils.i18n import format_money, get_locally_formatted_datetime


class OrderListView(PicotableListView):
    model = Order
    default_columns = [
        Column("identifier", _(u"Order"), linked=True, filter_config=TextFilter(operator="startswith")),
        Column("order_date", _(u"Order Date"), display="format_order_date", filter_config=DateRangeFilter()),
        Column(
            "customer", _(u"Customer"), display="format_customer_name",
            filter_config=MultiFieldTextFilter(
                filter_fields=(
                    "customer__email", "customer__name", "billing_address__name",
                    "shipping_address__name", "orderer__name"
                )
            )
        ),
        Column(
            "status", _(u"Status"), filter_config=ChoicesFilter(choices=OrderStatus.objects.all()),
        ),
        Column("payment_status", _(u"Payment Status"), filter_config=ChoicesFilter(choices=PaymentStatus.choices)),
        Column("shipping_status", _(u"Shipping Status"), filter_config=ChoicesFilter(choices=ShippingStatus.choices)),
        Column(
            "taxful_total_price_value", _(u"Total"), sort_field="taxful_total_price_value",
            display="format_taxful_total_price", class_name="text-right",
            filter_config=RangeFilter(field_type="number", filter_field="taxful_total_price_value")
        ),
    ]
    related_objects = [
        ("shop", "shuup.core.models:Shop"),
        ("billing_address", "shuup.core.models:ImmutableAddress"),
        ("shipping_address", "shuup.core.models:ImmutableAddress"),
    ]
    mass_actions = [
        "shuup.admin.modules.orders.mass_actions:CancelOrderAction",
        "shuup.admin.modules.orders.mass_actions:OrderConfirmationPdfAction",
        "shuup.admin.modules.orders.mass_actions:OrderDeliveryPdfAction",
    ]
    toolbar_buttons_provider_key = "order_list_toolbar_provider"
    mass_actions_provider_key = "order_list_mass_actions_provider"

    def get_toolbar(self):
        toolbar = Toolbar([
            NewActionButton.for_model(
                Order, url=reverse("shuup_admin:order.new")
            ),
            SettingsActionButton.for_model(Order, return_url="order")
        ], view=self)
        return toolbar

    def get_queryset(self):
        return super(OrderListView, self).get_queryset().exclude(deleted=True).filter(shop=get_shop(self.request))

    def format_customer_name(self, instance, *args, **kwargs):
        return instance.get_customer_name() or ""

    def format_order_date(self, instance, *args, **kwargs):
        return get_locally_formatted_datetime(instance.order_date)

    def format_taxful_total_price(self, instance, *args, **kwargs):
        return escape(format_money(instance.taxful_total_price))

    def label(self, instance, *args, **kwargs):
        # format label to make it human readable
        return instance.label.replace("_", " ").title()

    def get_object_abstract(self, instance, item):
        return [
            {"text": "%s" % instance, "class": "header"},
            {"title": _(u"Total"), "text": item.get("taxful_total_price_value")},
            {"title": _(u"Status"), "text": item.get("status")}
        ]
# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect
from django.contrib import messages

from shuup.admin.shop_provider import get_shop
from shuup.admin.supplier_provider import get_supplier
from shuup.admin.toolbar import NewActionButton, SettingsActionButton, Toolbar
from shuup.admin.utils.picotable import (
    ChoicesFilter, Column, DateRangeFilter, MultiFieldTextFilter, RangeFilter,
    TextFilter
)
from shuup.admin.utils.views import PicotableListView
from shuup.core.models import Order, OrderStatus, PaymentStatus, ShippingStatus, Shipment, ShipmentStatus, ShipmentProduct
from shuup.utils.django_compat import reverse
from shuup.utils.i18n import format_money, get_locally_formatted_datetime


class OrderListView(PicotableListView):
    model = Order
    default_columns = [
        Column("identifier", _(u"Order"), linked=True, filter_config=TextFilter(operator="startswith")),
        Column("order_date", _(u"Order Date"), display="format_order_date", filter_config=DateRangeFilter()),
        Column(
            "customer", _(u"Customer"), display="format_customer_name",
            filter_config=MultiFieldTextFilter(
                filter_fields=(
                    "customer__email", "customer__name", "billing_address__name",
                    "shipping_address__name", "orderer__name"
                )
            )
        ),
        Column(
            "status", _(u"Status"), filter_config=ChoicesFilter(choices=OrderStatus.objects.all()),
        ),
        Column("payment_status", _(u"Payment Status"), filter_config=ChoicesFilter(choices=PaymentStatus.choices)),
        Column("shipping_status", _(u"Shipping Status"), filter_config=ChoicesFilter(choices=ShippingStatus.choices)),
        Column(
            "taxful_total_price_value", _(u"Total"), sort_field="taxful_total_price_value",
            display="format_taxful_total_price", class_name="text-right",
            filter_config=RangeFilter(field_type="number", filter_field="taxful_total_price_value")
        ),
    ]
    related_objects = [
        ("shop", "shuup.core.models:Shop"),
        ("billing_address", "shuup.core.models:ImmutableAddress"),
        ("shipping_address", "shuup.core.models:ImmutableAddress"),
    ]
    mass_actions = [
        "shuup.admin.modules.orders.mass_actions:CancelOrderAction",
        "shuup.admin.modules.orders.mass_actions:OrderConfirmationPdfAction",
        "shuup.admin.modules.orders.mass_actions:OrderDeliveryPdfAction",
    ]
    toolbar_buttons_provider_key = "order_list_toolbar_provider"
    mass_actions_provider_key = "order_list_mass_actions_provider"

    def get_toolbar(self):
        toolbar = Toolbar([
            NewActionButton.for_model(
                Order, url=reverse("shuup_admin:order.new")
            ),
            SettingsActionButton.for_model(Order, return_url="order")
        ], view=self)
        return toolbar

    def get_queryset(self):
        return super(OrderListView, self).get_queryset().exclude(deleted=True).filter(shop=get_shop(self.request))

    def format_customer_name(self, instance, *args, **kwargs):
        return instance.get_customer_name() or ""

    def format_order_date(self, instance, *args, **kwargs):
        return get_locally_formatted_datetime(instance.order_date)

    def format_taxful_total_price(self, instance, *args, **kwargs):
        return escape(format_money(instance.taxful_total_price))

    def label(self, instance, *args, **kwargs):
        # format label to make it human readable
        return instance.label.replace("_", " ").title()

    def get_object_abstract(self, instance, item):
        return [
            {"text": "%s" % instance, "class": "header"},
            {"title": _(u"Total"), "text": item.get("taxful_total_price_value")},
            {"title": _(u"Status"), "text": item.get("status")}
        ]


class ShipmentListView(PicotableListView):
    model = Shipment
    default_columns = [
        Column("id", _(u"ID"), linked=True),
        Column("order_id", _(u"Order"), display="get_order_name", raw=True),
        Column("get_content", _(u"Content"), display="get_content", raw=True),
        Column("supplier_id", _(u"Supplier"), display="get_supplier", raw=True),
        Column("tracking_code", _(u"Tracking Code"), display="tracking_code_url", raw=True),
        Column("status", _(u"Status"), display="create_action_buttons", raw=True),
    ]

    def get_context_data(self):
        context = super(ShipmentListView, self).get_context_data()
        context["listview"] = True
        return context

    def tracking_code_url(self, instance):
        if instance.tracking_url:
            return f"<a href='{instance.tracking_url}'>{instance.tracking_code}</a>"
        return instance.tracking_code

    def get_supplier(self, instance):
        return instance.supplier.name

    def get_order_name(self, instance):
        return instance.order.__str__()

    def get_content(self, instance):
        query = ShipmentProduct.objects.filter(shipment=instance)
        product = ""
        for i in query:
            product = product + f"{i.product} ({i.quantity})"
        return product

    def create_action_buttons(self, instance):
        if instance.status == ShipmentStatus.SENT:
            return instance.status.name
        return f'<a class="btn btn-info btn-sm set_shipment_status" \
            href="{reverse("shuup_admin:order.shipments-list")}" shipment_id="{instance.id}" \
            onclick="handleSetSent(event, this)"><i class="fa fa-truck"></i> Mark as sent</a>'

    def __init__(self):
        super(ShipmentListView, self).__init__()
        self.columns = self.default_columns
    def get_queryset(self):
        if get_supplier(self.request) is None:
            return super(ShipmentListView, self).get_queryset().exclude(status=ShipmentStatus.DELETED)
        return super(ShipmentListView, self).get_queryset().exclude(status=ShipmentStatus.DELETED).filter(supplier=get_supplier(self.request))

    def get_object_abstract(self, instance, item):
        return [
            {"text": "%s" % instance, "class": "header"},
            {"title": _(u"Content"), "text": item.get("get_content")},
        ]
    def post(self, request, *args, **kwargs):
        shipment = Shipment.objects.get(pk=request.POST['shipment_id'])
        shipment.set_sent()
        message = _(f"Shipment status changed to {ShipmentStatus.SENT}.")
        messages.success(self.request, message)
        return HttpResponseRedirect(reverse("shuup_admin:order.shipments-list"))
