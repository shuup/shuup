# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
"""
Utilities for caching price info
"""
from shuup.core.pricing import PriceInfo
from shuup.core.utils import context_cache
from shuup.utils.dates import to_timestamp

PRICE_INFO_NAMESPACE_ITEM = "price_info_%(shop_id)s"


def _get_price_info_namespace_for_shop(shop_id):
    return PRICE_INFO_NAMESPACE_ITEM % dict(shop_id=shop_id)


def _get_price_info_cache_key_params(context, item, quantity, **context_args):
    shop_id = context.shop.pk if hasattr(context, "shop") else 0
    return dict(
        identifier="price_info_cache",
        item=_get_price_info_namespace_for_shop(shop_id),
        context={
            "customer": getattr(context, "customer", None)
        },
        quantity=quantity,
        context_item=item,
        **context_args
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

    key = context_cache.get_cache_key_for_context(
        many=True,
        **_get_price_info_cache_key_params(context, item, quantity, **context_args)
    )
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
    key, prices_infos = context_cache.get_cached_value(
        many=True,
        **_get_price_info_cache_key_params(context, item, quantity, **context_args)
    )

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
    key, price_info = context_cache.get_cached_value(
        **_get_price_info_cache_key_params(context, item, quantity, **context_args)
    )

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


def bump_prices_for_product(product):
    for shop_id in set(product.shop_products.values_list("shop", flat=True)):
        bump_price_info_cache(shop_id)


def bump_prices_for_shop_product(shop_product):
    bump_price_info_cache(shop_product.shop_id)
