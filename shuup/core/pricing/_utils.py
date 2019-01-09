# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from ._discounts import get_discount_modules
from ._module import get_pricing_module


def get_price_info(context, product, quantity=1):
    """
    Get price info of product for given quantity.

    Returned `PriceInfo` object contains calculated `price` and
    `base_price`.  The calculation of prices is handled in the
    current pricing module and possibly configured discount modules.

    :type context: shuup.core.pricing.PricingContextable
    :param product: `Product` object or id of `Product`
    :type product: shuup.core.models.Product|int
    :type quantity: int
    :rtype: shuup.core.pricing.PriceInfo
    """
    (mod, ctx) = _get_module_and_context(context)
    price_info = mod.get_price_info(ctx, product, quantity)
    for module in get_discount_modules():
        price_info = module.discount_price(ctx, product, price_info)
    return price_info


def get_pricing_steps(context, product):
    """
    Get context-specific list pricing steps for the given product.

    Returns a list of PriceInfos, see `PricingModule.get_pricing_steps`
    for description of its format.

    :type context: shuup.core.pricing.PricingContextable
    :param product: Product or product id
    :type product: shuup.core.models.Product|int
    :rtype: list[shuup.core.pricing.PriceInfo]
    """
    (mod, ctx) = _get_module_and_context(context)
    steps = mod.get_pricing_steps(ctx, product)
    for module in get_discount_modules():
        steps = module.get_pricing_steps(ctx, product, steps)
    return steps


def get_price_infos(context, products, quantity=1):
    """
    Get PriceInfo objects for a bunch of products.

    Returns a dict with product id as key and PriceInfo as value.

    May be faster than doing `get_price_info` for each product.

    :param products: List of product objects or id's
    :type products:  Iterable[shuup.core.models.Product|int]
    :rtype: dict[int,PriceInfo]
    """
    (mod, ctx) = _get_module_and_context(context)
    prices = mod.get_price_infos(ctx, products, quantity)
    for module in get_discount_modules():
        prices = module.discount_prices(ctx, products, prices)
    return prices


def get_pricing_steps_for_products(context, products):
    """
    Get pricing steps for a bunch of products.

    Returns a dict with product id as key and step data (as list of
    PriceInfos) as values.

    May be faster than doing `get_pricing_steps` for each product
    separately.

    :param products: List of product objects or id's
    :type products:  Iterable[shuup.core.models.Product|int]
    :rtype: dict[int,list[PriceInfo]]
    """
    (mod, ctx) = _get_module_and_context(context)
    steps = mod.get_pricing_steps_for_products(ctx, products)
    for module in get_discount_modules():
        steps = module.get_pricing_steps_for_products(ctx, products, steps)
    return steps


def _get_module_and_context(context):
    """
    Get current pricing module and context converted to pricing context.

    :type context: shuup.core.pricing.PricingContextable
    :rtype: (PricingModule,PricingContext)
    """
    pricing_mod = get_pricing_module()
    pricing_ctx = pricing_mod.get_context(context)
    return (pricing_mod, pricing_ctx)
