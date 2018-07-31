# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.db.models import Q

from shuup.core.models import Category

from .models import Discount


def get_potential_discounts_for_product(context, product):
    shop = context.shop
    product_id = product if isinstance(product, six.integer_types) else product.pk

    category_ids = Category.objects.filter(shop_products__product_id=product_id).values_list("id", flat=True)
    group_ids = context.customer.groups.values_list("id", flat=True)

    # Product condition is always applied
    condition_query = (Q(product__isnull=True) | Q(product_id=product_id))

    # Apply category conditions
    condition_query &= (
        Q(category__isnull=True) |
        (Q(exclude_selected_category=False) & Q(category__id__in=category_ids)) |
        (Q(exclude_selected_category=True) & ~Q(category__id__in=category_ids))
    )

    # Apply contact conditions
    condition_query &= (Q(contact__isnull=True) | Q(contact_id=context.customer.pk))

    # Apply contact group conditions
    condition_query &= (
        Q(contact_group__isnull=True) |
        (Q(exclude_selected_contact_group=False) & Q(contact_group__id__in=group_ids)) |
        (Q(exclude_selected_contact_group=True) & ~Q(contact_group__id__in=group_ids))
    )

    # Apply coupon code condition
    basket = getattr(context, "basket", None)
    if basket and basket.codes:
        coupon_queries = Q()
        for code in basket.codes:  # TODO: Revise! Likely there is not too many codes in basket.
            coupon_queries |= Q(
                Q(coupon_code__active=True) &
                Q(coupon_code__code__iexact=code)
            )

        condition_query &= (
            Q(coupon_code__isnull=True) |
            coupon_queries
        )
    else:
        condition_query &= Q(coupon_code__isnull=True)

    # Get all possible discounts for the current product and context
    return Discount.objects.available(shop).filter(
        condition_query
    ).values_list(
        "discounted_price_value", "discount_amount_value", "discount_percentage", "coupon_code__code"
    ).distinct()


def get_active_discount_for_code(order_or_order_source, code):
    shop = order_or_order_source.shop
    return Discount.objects.available(shop).filter(
        Q(coupon_code__active=True) &
        Q(coupon_code__code__iexact=code)
    ).first()
