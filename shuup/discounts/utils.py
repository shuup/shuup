# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.conf import settings
from django.db.models import Q
from typing import TYPE_CHECKING, Iterable

from shuup.core.models import (
    AnonymousContact,
    ProductCatalogDiscountedPrice,
    ProductCatalogDiscountedPriceRule,
    ShopProduct,
    Supplier,
)
from shuup.core.pricing import PricingContext
from shuup.core.utils import context_cache
from shuup.utils.dates import to_timestamp

if TYPE_CHECKING:  # pragma: no cover
    from shuup.discounts.models import Discount


def _get_price_expiration_cache_key(shop_id):
    return "price_expiration_%s" % shop_id


def get_potential_discounts_for_product(context, product, available_only=True, groups_ids=None, all_contacts=False):
    """
    Get a queryset of all possible discounts for a given context and product

    If `available_only` is True, only the discounts which match
        happy hours, start/end dates will be returned

    If `available_only` is False, all discounts that match with the context and product,
        that are active will be returned.
    """
    shop = context.shop
    product_id = product if isinstance(product, six.integer_types) else product.pk

    category_ids = set(
        [
            category_id
            for category_id in ShopProduct.objects.filter(product_id=product_id, shop=context.shop).values_list(
                "categories__id", flat=True
            )
            if category_id
        ]
    )
    group_ids = groups_ids if groups_ids else list(context.customer.groups_ids)

    # Product condition is always applied
    condition_query = Q(product__isnull=True) | Q(product_id=product_id)

    # Supplier condition is always applied
    supplier = context.supplier
    if supplier:
        condition_query &= Q(supplier=supplier) | Q(supplier__isnull=True)
    else:
        # No supplier in context means no discounts limited to specific
        # suppliers
        condition_query &= Q(supplier__isnull=True)

    # Apply category conditions
    if category_ids:
        condition_query &= (
            Q(category__isnull=True)
            | (Q(exclude_selected_category=False) & Q(category__id__in=category_ids))
            | (Q(exclude_selected_category=True) & ~Q(category__id__in=category_ids))
        )
    else:
        condition_query &= Q(category__isnull=True) | Q(exclude_selected_category=True, category__isnull=False)

    # Apply contact conditions
    if not all_contacts:
        if context.customer:
            condition_query &= Q(contact__isnull=True) | Q(contact=context.customer)
        else:
            condition_query &= Q(contact__isnull=True)

    if group_ids:
        # Apply contact group conditions
        condition_query &= Q(Q(contact_group__isnull=True) | Q(contact_group__id__in=group_ids))
    else:
        condition_query &= Q(contact_group__isnull=True)

    from shuup.discounts.models import Discount

    if available_only:
        base_queryset = Discount.objects.available(shop)
    else:
        base_queryset = Discount.objects.filter(shop=shop, active=True)

    # Get all possible discounts for the current product and context
    return base_queryset.filter(condition_query).distinct()


def get_active_discount_for_code(order_or_order_source, code):
    from shuup.discounts.models import Discount

    shop = order_or_order_source.shop
    return Discount.objects.available(shop).first()


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
        next_date.replace(hour=to_hour.hour, minute=to_hour.minute),
    ]

    # the next date is the same as today, let's return also the next week ranges
    if next_date.date() == now().date():
        next_week_date = next_date + datetime.timedelta(days=7)
        ranges.extend(
            [
                next_week_date.replace(hour=from_hour.hour, minute=from_hour.minute),
                next_week_date.replace(hour=to_hour.hour, minute=to_hour.minute),
            ]
        )

    return ranges


def bump_price_expiration(shop_ids: Iterable[int]):
    """
    Bump price expiration cache for shop ids
    """
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
            ]
            if event_date > now
        )

    :rtype numbers.Number|None
    :returns the price expiration time timestamp
    """
    cache_params = dict(
        identifier="price_expiration", item=_get_price_expiration_cache_key(context.shop.pk), context={}
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

    from shuup.discounts.models import Discount, TimeRange

    if settings.SHUUP_DISCOUNTS_PER_PRODUCT_EXPIRATION_DATES:
        potential_discounts = get_potential_discounts_for_product(context, product, available_only=False)
    else:
        potential_discounts = Discount.objects.active(context.shop)

    event_dates = []

    time_ranges = TimeRange.objects.filter(happy_hour__discounts__in=potential_discounts).distinct()
    for weekday, from_hour, to_hour in time_ranges.values_list("weekday", "from_hour", "to_hour"):
        event_dates.extend(get_next_dates_for_range(weekday, from_hour, to_hour))

    from django.utils.timezone import now

    now_datetime = now()

    if event_dates:
        min_event_date = min(event_date for event_date in event_dates if event_date > now_datetime)
        min_event_date_timestamp = to_timestamp(min_event_date)

        # cache the value in the context cache, setting the timeout as the price expiration time
        cache_timeout = max((min_event_date - now_datetime).total_seconds(), 0)
        context_cache.set_cached_value(key, min_event_date_timestamp, timeout=cache_timeout)

        # cache the context in the context, so if it is used again it will contain the calculated value
        setattr(context, context_cache_key, min_event_date_timestamp)

        return min_event_date_timestamp


def index_related_discount_shop_products(discounts: "Iterable[Discount]"):  # noqa: C901
    """
    Index all shop products that are affected by the given discounts
    """
    from shuup.discounts.modules import ProductDiscountModule

    indexed_shop_products = set()

    for discount in discounts:
        discounts_groups_ids = [AnonymousContact.get_default_group().pk]

        if discount.contact_group:
            discounts_groups_ids.append(discount.contact_group_id)

        shop_products = (
            ShopProduct.objects.select_related("shop", "product")
            .prefetch_related("suppliers")
            .filter(shop=discount.shop)
        )

        if discount.supplier:
            shop_products = shop_products.filter(suppliers=discount.supplier)

        if discount.product:
            shop_products = shop_products.filter(product=discount.product)

        if discount.category:
            if discount.exclude_selected_category:
                shop_products = shop_products.exclude(categories=discount.category)
            else:
                shop_products = shop_products.filter(categories=discount.category)

        # reindex all products that will be affected by this discount
        for shop_product in shop_products:
            if shop_product.pk in indexed_shop_products:
                continue

            indexed_shop_products.add(shop_product.pk)

            ProductCatalogDiscountedPrice.objects.filter(
                catalog_rule__module_identifier=ProductDiscountModule.identifier,
                shop=shop_product.shop,
                product=shop_product.product,
            ).delete()

            suppliers = shop_product.suppliers.all()
            if discount.supplier:
                suppliers = suppliers.filter(pk=discount.supplier_id)

            for supplier in suppliers:
                index_shop_product_price(shop_product, supplier, discounts_groups_ids)

        index_linked_shop_products(discount, discounts_groups_ids, indexed_shop_products)


def index_linked_shop_products(discount, discounts_groups_ids=[], ignore_shop_products_ids=[]):
    """
    Reindex all shop products previously linked
    this is required when a shop product shouldn't be linked anymore
    """
    from shuup.discounts.models import ShopProductCatalogDiscountsLink
    from shuup.discounts.modules import ProductDiscountModule

    discounts_links = (
        ShopProductCatalogDiscountsLink.objects.select_related("shop_product")
        .filter(Q(discounts=discount), ~Q(shop_product__in=ignore_shop_products_ids))
        .distinct()
    )

    for discounts_link in discounts_links:
        if discounts_link.shop_product_id in ignore_shop_products_ids:
            continue

        ignore_shop_products_ids.add(discounts_link.shop_product_id)

        ProductCatalogDiscountedPrice.objects.filter(
            catalog_rule__module_identifier=ProductDiscountModule.identifier,
            shop=discounts_link.shop_product.shop_id,
            product=discounts_link.shop_product.product_id,
        ).delete()

        for supplier in discounts_link.shop_product.suppliers.all():
            index_shop_product_price(discounts_link.shop_product, supplier, discounts_groups_ids)


def index_shop_product_price(
    shop_product: ShopProduct,
    supplier: Supplier,
    contact_groups_ids: Iterable[int] = [],
):
    """
    Index discounts for the shop product
    """
    from shuup.discounts.models import ShopProductCatalogDiscountsLink
    from shuup.discounts.modules import ProductDiscountModule

    default_price = shop_product.default_price_value
    context = PricingContext(shop=shop_product.shop, customer=AnonymousContact(), supplier=supplier)
    discounts = get_potential_discounts_for_product(
        context, shop_product.product, available_only=False, groups_ids=contact_groups_ids, all_contacts=True
    )

    # link this shop product to the potencial discounts
    discounts_link = ShopProductCatalogDiscountsLink.objects.get_or_create(shop_product=shop_product)[0]
    discounts_link.discounts.set(discounts)

    if not discounts.exists():
        # delete all discounted prices
        ProductCatalogDiscountedPrice.objects.filter(
            product=shop_product.product,
            shop=shop_product.shop,
            catalog_rule__module_identifier=ProductDiscountModule.identifier,
        ).delete()

    for discount in discounts:
        discount_options = [default_price]

        if discount.discounted_price_value is not None:
            discount_options.append(discount.discounted_price_value)

        if discount.discount_amount_value is not None:
            discount_options.append(default_price - discount.discount_amount_value)

        if discount.discount_percentage is not None:
            discount_options.append(default_price - (default_price * discount.discount_percentage))

        best_discounted_price = max(min(discount_options), 0)
        happy_hours_times = list(
            discount.happy_hours.values_list(
                "time_ranges__from_hour",
                "time_ranges__to_hour",
                "time_ranges__weekday",
            )
        )

        # if ther is no happy hour configured,
        # let's create one rule without time constraints
        if not happy_hours_times:
            happy_hours_times.append((None, None, None))

        for from_hour, to_hour, weekday in happy_hours_times:
            catalog_rule = ProductCatalogDiscountedPriceRule.objects.get_or_create(
                module_identifier=ProductDiscountModule.identifier,
                contact_group=discount.contact_group,
                contact=discount.contact,
                valid_start_date=discount.start_datetime,
                valid_end_date=discount.end_datetime,
                valid_start_hour=from_hour,
                valid_end_hour=to_hour,
                valid_weekday=weekday,
            )[0]
            ProductCatalogDiscountedPrice.objects.update_or_create(
                product=shop_product.product,
                shop=shop_product.shop,
                supplier=supplier,
                catalog_rule=catalog_rule,
                defaults=dict(discounted_price_value=best_discounted_price),
            )
