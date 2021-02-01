# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.conf import settings
from django.db.models import Q

from shuup.core.models import Category
from shuup.core.utils import context_cache
from shuup.utils.dates import to_timestamp


def _get_price_expiration_cache_key(shop_id):
    return "price_expiration_%s" % shop_id


def get_potential_discounts_for_product(context, product, available_only=True):
    """
    Get a queryset of all possible discounts for a given context and product

    If `available_only` is True, only the discounts which match
        happy hours, availability exceptions and start/end dates will be returned

    If `available_only` is False, all discounts that match with the context and product,
        that are active will be returned.
    """
    shop = context.shop
    product_id = product if isinstance(product, six.integer_types) else product.pk

    category_ids = list(Category.objects.filter(shop_products__product_id=product_id).values_list("id", flat=True))
    group_ids = list(context.customer.groups.values_list("id", flat=True))

    # Product condition is always applied
    condition_query = (Q(product__isnull=True) | Q(product_id=product_id))

    # Supplier condition is always applied
    supplier = context.supplier
    if supplier:
        condition_query &= (Q(supplier=supplier) | Q(supplier__isnull=True))
    else:
        # No supplier in context means no discounts limited to specific
        # suppliers
        condition_query &= Q(supplier__isnull=True)

    # Apply category conditions
    if len(category_ids) == 1:
        condition_query &= (
            Q(category__isnull=True) |
            (Q(exclude_selected_category=False) & Q(category__id=category_ids[0])) |
            (Q(exclude_selected_category=True) & ~Q(category__id=category_ids[0]))
        )
    else:
        condition_query &= (
            Q(category__isnull=True) |
            (Q(exclude_selected_category=False) & Q(category__id__in=category_ids)) |
            (Q(exclude_selected_category=True) & ~Q(category__id__in=category_ids))
        )

    # Apply contact conditions
    condition_query &= (Q(contact__isnull=True) | Q(contact_id=context.customer.pk))

    # Apply contact group conditions
    if len(group_ids) == 1:
        condition_query &= (
            Q(contact_group__isnull=True) |
            (Q(exclude_selected_contact_group=False) & Q(contact_group__id=group_ids[0])) |
            (Q(exclude_selected_contact_group=True) & ~Q(contact_group__id=group_ids[0]))
        )
    else:
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

    from shuup.discounts.models import Discount
    if available_only:
        base_queryset = Discount.objects.available(shop)
    else:
        base_queryset = Discount.objects.filter(shops=shop, active=True)

    # Get all possible discounts for the current product and context
    return base_queryset.filter(condition_query).distinct()


def get_active_discount_for_code(order_or_order_source, code):
    from shuup.discounts.models import Discount
    shop = order_or_order_source.shop
    return Discount.objects.available(shop).filter(
        Q(coupon_code__active=True) &
        Q(coupon_code__code__iexact=code)
    ).first()


def get_next_dates_for_range(weekday, from_hour, to_hour):
    """
    Get datetime ranges for the next weekday

    Example:
        Give me the date ranges for the next Sunday from 1pm to 10pm
        It will return a tuple of datetimes.

    If the requested weekday is the same of today, it will return both the ranges for today
        and also for the next week.

    :rtype list[datetime.datetime]
    """
    import datetime
    from django.utils.timezone import now

    now_datetime = now()
    next_date = now_datetime + datetime.timedelta(days=(abs(weekday - now_datetime.weekday()) % 7))
    ranges = [
        next_date.replace(hour=from_hour.hour, minute=from_hour.minute),
        next_date.replace(hour=to_hour.hour, minute=to_hour.minute)
    ]

    # the next date is the same as today, let's return also the next week ranges
    if next_date.date() == now().date():
        next_week_date = next_date + datetime.timedelta(days=7)
        ranges.extend([
            next_week_date.replace(hour=from_hour.hour, minute=from_hour.minute),
            next_week_date.replace(hour=to_hour.hour, minute=to_hour.minute)
        ])

    return ranges


def bump_price_expiration(shops):
    """
    Bump price expiration cache for shops

    :param itetable[int|Shop] shops: list of shops to bump caches
    """
    from shuup.core.models import Shop
    shop_ids = [shop.pk if isinstance(shop, Shop) else int(shop) for shop in shops]

    for shop_id in shop_ids:
        context_cache.bump_cache_for_item(_get_price_expiration_cache_key(shop_id))


def get_price_expiration(context, product):
    """
    Returns the price expiration for the product through a UNIX timestamp

    This routine loads all dates that can possibly affect the price of the product in the future.

    After fetching all the event dates, the expiration time will
        be the minimum datetime that is greater than now:

        expire_on = min(
            event_date for event_dates in [
                next_discount_start,
                next_discount_ends,
                next_happy_hour_start,
                next_happy_hour_end,
                next_availability_exception_start,
                next_availability_exception_end
            ]
            if event_date > now
        )

    :rtype numbers.Number|None
    :returns the price expiration time timestamp
    """
    cache_params = dict(
        identifier="price_expiration",
        item=_get_price_expiration_cache_key(context.shop.pk),
        context={}
    )

    if settings.SHUUP_DISCOUNTS_PER_PRODUCT_EXPIRATION_DATES:
        cache_params["customer"] = getattr(context, "customer", None)
        cache_params["product"] = product

    key, value = context_cache.get_cached_value(**cache_params)
    if value is not None:
        return value

    context_cache_key = "price_expiration_%(shop_id)s" % dict(shop_id=context.shop.pk)
    if hasattr(context, "context_cache_key"):
        return getattr(context, context_cache_key)

    from shuup.discounts.models import AvailabilityException, Discount, TimeRange

    if settings.SHUUP_DISCOUNTS_PER_PRODUCT_EXPIRATION_DATES:
        potential_discounts = get_potential_discounts_for_product(context, product, available_only=False)
    else:
        potential_discounts = Discount.objects.active(context.shop)

    event_dates = []

    availability_exceptions = AvailabilityException.objects.filter(discounts__in=potential_discounts).distinct()
    for start_datetime, end_datetime in availability_exceptions.values_list("start_datetime", "end_datetime"):
        event_dates.extend([start_datetime, end_datetime])

    time_ranges = TimeRange.objects.filter(happy_hour__discounts__in=potential_discounts).distinct()
    for weekday, from_hour, to_hour in time_ranges.values_list("weekday", "from_hour", "to_hour"):
        event_dates.extend(get_next_dates_for_range(weekday, from_hour, to_hour))

    from django.utils.timezone import now
    now_datetime = now()

    if event_dates:
        min_event_date = (
            min(event_date for event_date in event_dates if event_date > now_datetime)
        )
        min_event_date_timestamp = to_timestamp(min_event_date)

        # cache the value in the context cache, setting the timeout as the price expiration time
        cache_timeout = max((min_event_date - now_datetime).total_seconds(), 0)
        context_cache.set_cached_value(key, min_event_date_timestamp, timeout=cache_timeout)

        # cache the context in the context, so if it is used again it will contain the calculated value
        setattr(context, context_cache_key, min_event_date_timestamp)

        return min_event_date_timestamp
