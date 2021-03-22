# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from typing import Union

from shuup.core.models import Shop

LISTED_PRODUCTS_CACHE_ITEM_FMT = "listed_products_objs-{shop_id}"
BEST_SELLING_PRODUCTS_CACHE_ITEM_FMT = "best_selling_products_objs-{shop_id}"
NEWEST_PRODUCTS_CACHE_ITEM_FMT = "newest_products_objs-{shop_id}"
RANDOM_PRODUCTS_CACHE_ITEM_FMT = "random_products_objs-{shop_id}"
PRODUCTS_FOR_CATEGORY_CACHE_ITEM_FMT = "products_for_category_objs-{shop_id}"
ALL_MANUFACTURERS_CACHE_ITEM_FMT = "all_manufacturers_objs-{shop_id}"
CROSS_SELLS_CACHE_ITEM_FMT = "cross_sells_objs-{shop_id}"


def get_listed_products_cache_item(shop: Union[Shop, int]):
    shop_id = shop.id if hasattr(shop, "pk") else shop
    return LISTED_PRODUCTS_CACHE_ITEM_FMT.format(shop_id=shop_id)


def get_best_selling_products_cache_item(shop: Union[Shop, int]):
    shop_id = shop.id if hasattr(shop, "pk") else shop
    return BEST_SELLING_PRODUCTS_CACHE_ITEM_FMT.format(shop_id=shop_id)


def get_newest_products_cache_item(shop: Union[Shop, int]):
    shop_id = shop.id if hasattr(shop, "pk") else shop
    return NEWEST_PRODUCTS_CACHE_ITEM_FMT.format(shop_id=shop_id)


def get_random_products_cache_item(shop: Union[Shop, int]):
    shop_id = shop.id if hasattr(shop, "pk") else shop
    return RANDOM_PRODUCTS_CACHE_ITEM_FMT.format(shop_id=shop_id)


def get_products_for_category_cache_item(shop: Union[Shop, int]):
    shop_id = shop.id if hasattr(shop, "pk") else shop
    return PRODUCTS_FOR_CATEGORY_CACHE_ITEM_FMT.format(shop_id=shop_id)


def get_all_manufacturers_cache_item(shop: Union[Shop, int]):
    shop_id = shop.id if hasattr(shop, "pk") else shop
    return ALL_MANUFACTURERS_CACHE_ITEM_FMT.format(shop_id=shop_id)


def get_cross_sells_cache_item(shop: Union[Shop, int]):
    shop_id = shop.id if hasattr(shop, "pk") else shop
    return CROSS_SELLS_CACHE_ITEM_FMT.format(shop_id=shop_id)
