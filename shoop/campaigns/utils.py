# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django.db.models import Q, Sum

from shoop.core.models import Payment


def get_total_sales(shop, customer):
    aggregated_sales = Payment.objects.filter(
        order__customer=customer,
        order__shop=shop,
    ).aggregate(total_sales=Sum("amount_value"))
    return aggregated_sales["total_sales"] or 0


def assign_to_group_based_on_sales(cls, shop, customer, sales_range=None):
    total_sales = get_total_sales(shop, customer)

    # Only ranges with sales bigger than min_value
    query = Q(min_value__lte=total_sales)
    # Ranges with max lower than sales or None
    query &= Q(Q(max_value__gt=total_sales) | Q(max_value__isnull=True))

    qs = cls.objects.active(shop)
    if sales_range:
        qs = qs.filter(pk=sales_range.pk)

    matching_pks = set(qs.filter(query).values_list("pk", flat=True))
    for sales_range in cls.objects.filter(pk__in=matching_pks):
        sales_range.group.members.add(customer)

    for sales_range in cls.objects.active(shop).exclude(pk__in=matching_pks):
        sales_range.group.members.remove(customer)
