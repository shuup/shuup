# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
"""
Utilities for caching price info
"""
from decimal import Decimal

from shuup.core.models import AnonymousContact, ShopProduct
from shuup.core.pricing import PriceInfo
from shuup.core.utils import context_cache
from shuup.utils.dates import to_timestamp

PRICE_INFO_NAMESPACE_ITEM = "price_info_%(shop_id)s"


def _get_price_info_namespace_for_shop(shop_id):
    return PRICE_INFO_NAMESPACE_ITEM % dict(shop_id=shop_id)


def _get_price_info_cache_key_params(context, item, quantity, **context_args):
    shop_id = context.shop.pk if hasattr(context, "shop") else 0
    customer = getattr(context, "customer", None)

    if customer:
        cached_customer_groups = getattr(customer, "_cached_customer_groups", None)
        if cached_customer_groups:
            groups = customer._cached_customer_groups
        else:
            groups = list(customer.groups.order_by("pk").values_list("pk", flat=True))
            customer._cached_customer_groups = groups
    else:
        anonymous_group_id = getattr(AnonymousContact, "_cached_default_group_id", None)
        if anonymous_group_id:
            groups = [AnonymousContact._cached_default_group_id]
        else:
            anonymous_group_id = AnonymousContact().default_group.pk
            AnonymousContact._cached_default_group_id = anonymous_group_id
            groups = [anonymous_group_id]

    extra_kwargs = dict()
    for key, value in context_args.items():
        if hasattr(value, "pk"):
            extra_kwargs[key] = value.pk
        else:
            extra_kwargs[key] = value

    return dict(
        identifier="price_info_cache",
        item=_get_price_info_namespace_for_shop(shop_id),
        context={},
        customer_groups=groups,
        quantity=str(Decimal(quantity)),
        item_id=item.pk if hasattr(item, "pk") else str(item),
        **extra_kwargs
    )


def cache_many_price_info(context, item, quantity, prices_infos, **context_args):
    """
    Cache a list of PriceInfo

    :param object|WSGIRequest context: the context should contain at least a shop and a customer property
    :param object item
    :param float|Decimal quantity
    :param iterable[PriceInfo] prices_infos
    """
    # check whether the prices are iterable
    try:
        iter(prices_infos)
    except TypeError:
        return

    # all items must be PriceInfo
    if not all(isinstance(item, PriceInfo) for item in prices_infos):
        return

    context_kwargs = _get_price_info_cache_key_params(context, item, quantity, **context_args)
    key = context_cache.get_cache_key_for_context(many=True, **context_kwargs)
    context_cache.set_cached_value(key, prices_infos)


def cache_price_info(context, item, quantity, price_info, **context_args):
    """
    Cache a PriceInfo

    :param context object|WSGIRequest: the context should contain at least a shop and a customer property
    :param item any
    :param quantity float|Decimal
    :param price_info PriceInfo
    """
    # we can just cache PriceInfo instances
    if isinstance(price_info, PriceInfo):
        key = context_cache.get_cache_key_for_context(
            **_get_price_info_cache_key_params(context, item, quantity, **context_args)
        )
        context_cache.set_cached_value(key, price_info)


def get_many_cached_price_info(context, item, quantity=1, **context_args):
    """
    Get cached prices info list

    :param object|WSGIRequest context: the context should contain at least a shop and a customer property
    :param object item
    :param float|Decimal quantity
    """
    cache_kwargs = _get_price_info_cache_key_params(context, item, quantity, many=True, **context_args)
    key, prices_infos = context_cache.get_cached_value(**cache_kwargs)

    if prices_infos:
        try:
            iter(prices_infos)
        except TypeError:
            return None

        from django.utils.timezone import now

        now_timestamp = to_timestamp(now())

        # make sure to check all experiration dates
        for price_info in prices_infos:
            # if one price has expired, we invalidate the entire cache
            if isinstance(price_info, PriceInfo) and price_info.expires_on and price_info.expires_on < now_timestamp:
                return None

    return prices_infos


def get_cached_price_info(context, item, quantity=1, **context_args):
    """
    Get a cached price info

    :param object|WSGIRequest context: the context should contain at least a shop and a customer property
    :param object item
    :param float|Decimal quantity
    """
    cache_kwargs = _get_price_info_cache_key_params(context, item, quantity, **context_args)
    key, price_info = context_cache.get_cached_value(**cache_kwargs)

    from django.utils.timezone import now

    now_ts = to_timestamp(now())

    # price has expired
    if price_info and isinstance(price_info, PriceInfo) and price_info.expires_on and price_info.expires_on < now_ts:
        price_info = None

    return price_info


def bump_price_info_cache(shop):
    """
    Bump the price info cache for the entire shop

    :param int|Shop shop: the shop to be bump caches
    """
    from shuup.core.models import Shop

    shop_id = shop.pk if isinstance(shop, Shop) else int(shop)
    context_cache.bump_cache_for_item(_get_price_info_namespace_for_shop(shop_id))


def bump_all_price_caches(shops=[]):
    """
    Bump all price info caches for the given shops or all shops

    :param list[int|Shop]|None shops: the shops list to be bump caches or None to bump all
    """
    from shuup.core.models import Shop

    if shops:
        shop_ids = [shop.pk if isinstance(shop, Shop) else int(shop) for shop in shops]
    else:
        shop_ids = Shop.objects.values_list("pk", flat=True)

    for shop_id in shop_ids:
        bump_price_info_cache(shop_id)


def bump_prices_for_product(product_id):
    if hasattr(product_id, "pk"):
        product_id = product_id.pk
    for shop_id in set(ShopProduct.objects.filter(product_id=product_id).values_list("shop_id", flat=True)):
        bump_price_info_cache(shop_id)


def bump_prices_for_shop_product(shop_id):
    if isinstance(shop_id, ShopProduct):
        shop_id = shop_id.shop_id
    bump_price_info_cache(shop_id)
