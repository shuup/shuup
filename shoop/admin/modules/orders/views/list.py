# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from babel.dates import format_datetime
from django.utils.html import escape
from django.utils.timezone import localtime
from django.utils.translation import ugettext as _

from shoop.admin.utils.picotable import (
    ChoicesFilter, Column, DateRangeFilter, MultiFieldTextFilter, RangeFilter,
    TextFilter
)
from shoop.admin.utils.views import PicotableListView
from shoop.core.models import Order, OrderStatus, PaymentStatus, ShippingStatus
from shoop.utils.i18n import format_money, get_current_babel_locale


class OrderListView(PicotableListView):
    model = Order
    columns = [
        Column("identifier", _(u"Order"), linked=True, filter_config=TextFilter(operator="startswith")),
        Column("order_date", _(u"Order Date"), display="format_order_date", filter_config=DateRangeFilter()),
        Column(
            "customer", _(u"Customer"),
            filter_config=MultiFieldTextFilter(filter_fields=("customer__email", "customer__name"))
        ),
        Column("status", _(u"Status"), filter_config=ChoicesFilter(choices=OrderStatus.objects.all())),
        Column("payment_status", _(u"Payment Status"), filter_config=ChoicesFilter(choices=PaymentStatus.choices)),
        Column("shipping_status", _(u"Shipping Status"), filter_config=ChoicesFilter(choices=ShippingStatus.choices)),
        Column(
            "taxful_total_price", _(u"Total"), sort_field="taxful_total_price_value",
            display="format_taxful_total_price", class_name="text-right",
            filter_config=RangeFilter(field_type="number", filter_field="taxful_total_price_value")
        ),
    ]

    def get_queryset(self):
        return super(OrderListView, self).get_queryset().exclude(deleted=True)

    def format_order_date(self, instance, *args, **kwargs):
        return format_datetime(localtime(instance.order_date), locale=get_current_babel_locale())

    def format_taxful_total_price(self, instance, *args, **kwargs):
        return escape(format_money(instance.taxful_total_price))

    def get_object_abstract(self, instance, item):
        return [
            {"text": "%s" % instance, "class": "header"},
            {"title": _(u"Total"), "text": item["taxful_total_price"]},
            {"title": _(u"Status"), "text": item["status"]}
        ]
