# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
"""
Utilities for displaying prices correctly.

Contents:

  * Class `PriceDisplayOptions` for storing the display options.

  * Various filter classes for implementing Jinja2 filters.
"""

import django_jinja.library
import jinja2

from shoop.core.pricing import PriceDisplayOptions, Priceful
from shoop.core.templatetags.shoop_common import money, percent

from .prices import convert_taxness


class _ContextObject(object):
    def __init__(self, name, property_name=None):
        self.name = name
        self.property_name = (property_name or name)
        self._register()


class _ContextFilter(_ContextObject):
    def _register(self):
        django_jinja.library.filter(
            name=self.name,
            fn=jinja2.contextfilter(self))


class _ContextFunction(_ContextObject):
    def _register(self):
        django_jinja.library.global_function(
            name=self.name,
            fn=jinja2.contextfunction(self))


class PriceDisplayFilter(_ContextFilter):
    def __call__(self, context, item, quantity=1):
        options = PriceDisplayOptions.from_context(context)
        if options.hide_prices:
            return ""
        request = context.get('request')
        orig_priceful = _get_priceful(request, item, quantity)
        if not orig_priceful:
            return ""
        priceful = convert_taxness(
            request, item, orig_priceful, options.include_taxes)
        price_value = getattr(priceful, self.property_name)
        return money(price_value)


class PricePropertyFilter(_ContextFilter):
    def __call__(self, context, item, quantity=1):
        priceful = _get_priceful(context.get('request'), item, quantity)
        if not priceful:
            return ""
        return getattr(priceful, self.property_name)


class PricePercentPropertyFilter(_ContextFilter):
    def __call__(self, context, item, quantity=1):
        priceful = _get_priceful(context.get('request'), item, quantity)
        if not priceful:
            return ""
        return percent(getattr(priceful, self.property_name))


class TotalPriceDisplayFilter(_ContextFilter):
    def __call__(self, context, source):
        """
        :type source: shoop.core.order_creator.OrderSource|
                      shoop.core.models.Order
        """
        options = PriceDisplayOptions.from_context(context)
        if options.hide_prices:
            return ""
        try:
            if options.include_taxes is None:
                total = source.total_price
            elif options.include_taxes:
                total = source.taxful_total_price
            else:
                total = source.taxless_total_price
        except TypeError:
            total = source.total_price
        return money(total)


class PriceRangeDisplayFilter(_ContextFilter):
    def __call__(self, context, product, quantity=1):
        """
        :type product: shoop.core.models.Product
        """
        options = PriceDisplayOptions.from_context(context)
        if options.hide_prices:
            return ("", "")
        request = context.get('request')
        priced_children = product.get_priced_children(request, quantity)
        priced_products = priced_children if priced_children else [
            (product, _get_priceful(request, product, quantity))]

        def get_formatted_price(priced_product):
            (prod, price_info) = priced_product
            if not price_info:
                return ""
            pf = convert_taxness(
                request, prod, price_info, options.include_taxes)
            return money(pf.price)

        min_max = (priced_products[0], priced_products[-1])
        return tuple(get_formatted_price(x) for x in min_max)


def _get_priceful(request, item, quantity):
    """
    Get priceful from given item.

    If item has `get_price_info` method, it will be called with given
    `request` and `quantity` as arguments, otherwise the item itself
    should implement the `Priceful` interface.

    :type request: django.http.HttpRequest
    :type item: shoop.core.taxing.TaxableItem
    :type quantity: numbers.Number
    :rtype: shoop.core.pricing.Priceful|None
    """
    if hasattr(item, 'get_price_info'):
        if hasattr(item, 'is_variation_parent'):
            if item.is_variation_parent():
                return item.get_cheapest_child_price_info(request, quantity)
        return item.get_price_info(request, quantity=quantity)
    assert isinstance(item, Priceful)
    return item
