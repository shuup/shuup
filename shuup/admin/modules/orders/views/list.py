# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _

from shuup.admin.shop_provider import get_shop
from shuup.admin.toolbar import NewActionButton, SettingsActionButton, Toolbar
from shuup.admin.utils.picotable import (
    ChoicesFilter,
    Column,
    DateRangeFilter,
    MultiFieldTextFilter,
    RangeFilter,
    TextFilter,
)
from shuup.admin.utils.views import PicotableListView
from shuup.core.models import Order, OrderStatus, PaymentStatus, ShippingStatus
from shuup.utils.django_compat import reverse
from shuup.utils.i18n import format_money, get_locally_formatted_datetime


class OrderListView(PicotableListView):
    model = Order
    default_columns = [
        Column("identifier", _("Order"), linked=True, filter_config=TextFilter(operator="startswith")),
        Column("order_date", _("Order Date"), display="format_order_date", filter_config=DateRangeFilter()),
        Column(
            "customer",
            _("Customer"),
            display="format_customer_name",
            filter_config=MultiFieldTextFilter(
                filter_fields=(
                    "customer__email",
                    "customer__name",
                    "billing_address__name",
                    "shipping_address__name",
                    "orderer__name",
                )
            ),
        ),
        Column(
            "status",
            _("Status"),
            filter_config=ChoicesFilter(choices=OrderStatus.objects.all()),
        ),
        Column("payment_status", _("Payment Status"), filter_config=ChoicesFilter(choices=PaymentStatus.choices)),
        Column("shipping_status", _("Shipping Status"), filter_config=ChoicesFilter(choices=ShippingStatus.choices)),
        Column(
            "taxful_total_price_value",
            _("Total, incl. tax"),
            sort_field="taxful_total_price_value",
            display="format_taxful_total_price",
            class_name="text-right",
            filter_config=RangeFilter(field_type="number", filter_field="taxful_total_price_value"),
        ),
        Column(
            "taxless_total_price_value",
            _("Total, excl. tax"),
            sort_field="taxless_total_price_value",
            display="format_taxless_total_price",
            class_name="text-right",
            filter_config=RangeFilter(field_type="number", filter_field="taxless_total_price_value"),
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
        toolbar = Toolbar(
            [
                NewActionButton.for_model(Order, url=reverse("shuup_admin:order.new")),
                SettingsActionButton.for_model(Order, return_url="order"),
            ],
            view=self,
        )
        return toolbar

    def get_queryset(self):
        return super(OrderListView, self).get_queryset().exclude(deleted=True).filter(shop=get_shop(self.request))

    def format_customer_name(self, instance, *args, **kwargs):
        return instance.get_customer_name() or ""

    def format_order_date(self, instance, *args, **kwargs):
        return get_locally_formatted_datetime(instance.order_date)

    def format_taxful_total_price(self, instance, *args, **kwargs):
        return escape(format_money(instance.taxful_total_price))

    def format_taxless_total_price(self, instance, *args, **kwargs):
        return escape(format_money(instance.taxless_total_price))

    def label(self, instance, *args, **kwargs):
        # format label to make it human readable
        return instance.label.replace("_", " ").title()

    def get_object_abstract(self, instance, item):
        return [
            {"text": "%s" % instance, "class": "header"},
            {"title": _("Total, incl. tax"), "text": item.get("taxful_total_price_value")},
            {"title": _("Total, excl. tax"), "text": item.get("taxless_total_price_value")},
            {"title": _("Status"), "text": item.get("status")},
        ]
