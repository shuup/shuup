# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from ._module import get_pricing_module


def get_price_info(context, product, quantity=1):
    """
    Get price info of product for given quantity.

    Returned `PriceInfo` object contains calculated `price` and
    `base_price`.  The calculation of prices is handled in the
    current pricing module and possibly configured discount modules.

    :type context: shoop.core.pricing.PricingContextable
    :param product: `Product` object or id of `Product`
    :type product: shoop.core.models.Product|int
    :type quantity: int
    :rtype: shoop.core.pricing.PriceInfo
    """
    (mod, ctx) = _get_module_and_context(context)
    price_info = mod.get_price_info(ctx, product, quantity)
    return price_info


def get_pricing_steps(context, product):
    """
    Get context-specific list pricing steps for the given product.

    Returns a list of PriceInfos, see `PricingModule.get_pricing_steps`
    for description of its format.

    :type context: shoop.core.pricing.PricingContextable
    :param product: Product or product id
    :type product: shoop.core.models.Product|int
    :rtype: list[shoop.core.pricing.PriceInfo]
    """
    (mod, ctx) = _get_module_and_context(context)
    steps = mod.get_pricing_steps(ctx, product)
    return steps


def get_price_infos(context, products, quantity=1):
    """
    Get PriceInfo objects for a bunch of products.

    Returns a dict with product id as key and PriceInfo as value.

    May be faster than doing `get_price_info` for each product.

    :param products: List of product objects or id's
    :type products:  Iterable[shoop.core.models.Product|int]
    :rtype: dict[int,PriceInfo]
    """
    (mod, ctx) = _get_module_and_context(context)
    prices = mod.get_price_infos(ctx, products, quantity)
    return prices


def get_pricing_steps_for_products(context, products):
    """
    Get pricing steps for a bunch of products.

    Returns a dict with product id as key and step data (as list of
    PriceInfos) as values.

    May be faster than doing `get_pricing_steps` for each product
    separately.

    :param products: List of product objects or id's
    :type products:  Iterable[shoop.core.models.Product|int]
    :rtype: dict[int,list[PriceInfo]]
    """
    (mod, ctx) = _get_module_and_context(context)
    steps = mod.get_pricing_steps_for_products(ctx, products)
    return steps


def _get_module_and_context(context):
    """
    Get current pricing module and context converted to pricing context.

    :type context: shoop.core.pricing.PricingContextable
    :rtype: tuple[PricingModule,PricingContext]
    """
    pricing_mod = get_pricing_module()
    pricing_ctx = pricing_mod.get_context(context)
    return (pricing_mod, pricing_ctx)
