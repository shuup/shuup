# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.models import Q

from shuup.core.models import Order, OrderLine
from shuup.utils.dates import to_datetime_range


class OrderReportMixin(object):
    def get_objects(self, paid=True):
        (start, end) = to_datetime_range(self.start_date, self.end_date)
        queryset = Order.objects.filter(shop=self.shop, order_date__range=(start, end))
        creator = self.options.get("creator")
        orderer = self.options.get("orderer")
        customer = self.options.get("customer")
        filters = Q()
        if creator:
            filters &= Q(creator__in=creator)
        if orderer:
            filters &= Q(orderer__in=orderer)
        if customer:
            filters &= Q(customer__in=customer)
        queryset = queryset.filter(filters).valid()
        if paid:
            queryset = queryset.paid()
        return queryset.order_by("order_date")


class OrderLineReportMixin(object):
    def get_objects(self):
        (start, end) = to_datetime_range(self.start_date, self.end_date)
        queryset = OrderLine.objects.filter(created_on__range=(start, end))
        supplier = self.options.get("supplier")
        types = self.options.get("order_line_type")
        order_status = self.options.get("order_status")
        filters = Q()
        if supplier:
            filters &= Q(supplier__in=supplier)
        if types:
            filters &= Q(type__in=types)
        if order_status:
            filters &= Q(order__status__in=order_status)
        return queryset.filter(filters).order_by("created_on")
