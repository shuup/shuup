# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django.db.models import Q, Sum

from shoop.campaigns.models import ContactGroupSalesRange
from shoop.core.models import Payment


def _get_total_sales(shop, customer):
    aggregated_sales = Payment.objects.filter(
        order__customer=customer,
        order__shop=shop,
    ).aggregate(total_sales=Sum("amount_value"))
    return aggregated_sales["total_sales"] or 0


def _assign_to_group_based_on_sales(shop, customer):
    total_sales = _get_total_sales(shop, customer)

    # Only ranges with given shop
    query = Q(shop=shop)
    # Both min and max can't be zero for enabled range
    query &= ~Q(Q(min_value=0) & Q(max_value=0))
    # Min can't be null
    query &= Q(min_value__isnull=False)
    # Only ranges with sales bigger than min_value
    query &= Q(min_value__lte=total_sales)
    # Ranges with max lower than sales or None
    query &= Q(Q(max_value__gt=total_sales) | Q(max_value__isnull=True))

    matching_pks = set(ContactGroupSalesRange.objects.filter(query).values_list("pk", flat=True))
    for sales_level in ContactGroupSalesRange.objects.filter(pk__in=matching_pks):
        sales_level.group.members.add(customer)
    for sales_level in ContactGroupSalesRange.objects.exclude(pk__in=matching_pks):
        sales_level.group.members.remove(customer)


def update_customers_groups(sender, instance, **kwargs):
    if not instance.order.customer:
        return
    _assign_to_group_based_on_sales(instance.order.shop, instance.order.customer)
