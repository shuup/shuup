# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.models import Q, Sum

from shuup.core.models import Payment


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


def get_contacts_in_sales_range(shop, min_value, max_value):
    total_sales = Payment.objects.filter(
        order__shop=shop,
    ).values(
        "order__customer_id"
    ).annotate(
        total_sales=Sum("amount_value")
    )
    # Since https://github.com/django/django/commit/3bbaf84d6533fb61ac0038f2bbe52ee0d7b4fd10
    # is introduced in Django 1.9a1 we can't filter total sales with min and max value
    results = set()
    for result in total_sales:
        total_sales = result.get("total_sales")
        if min_value <= total_sales and (max_value is None or max_value > total_sales):
            results.add(result.get("order__customer_id"))
    return results
