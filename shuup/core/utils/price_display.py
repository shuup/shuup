# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
"""
Utilities for displaying prices correctly.

Contents:

  * Class `PriceDisplayOptions` for storing the display options.

  * Helper function `render_price_property` for rendering prices
    correctly from Python code.

  * Various filter classes for implementing Jinja2 filters.
"""

import django_jinja.library
import jinja2

from shuup.core.pricing import PriceDisplayOptions, Priceful
from shuup.core.templatetags.shuup_common import money, percent

from .prices import convert_taxness

PRICED_CHILDREN_CACHE_KEY = "%s-%s_priced_children"


def render_price_property(request, item, priceful, property_name='price'):
    """
    Render price property of a Priceful object.

    :type request: django.http.HttpRequest
    :type item: shuup.core.taxing.TaxableItem
    :type priceful: shuup.core.pricing.Priceful
    :type propert_name: str
    :rtype: str
    """
    options = PriceDisplayOptions.from_context({'request': request})
    if options.hide_prices:
        return ""
    new_priceful = convert_taxness(
        request, item, priceful, options.include_taxes)
    price_value = getattr(new_priceful, property_name)
    return money(price_value)


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

    @property
    def cache_identifier(self):
        return "price_filter_%s" % self.name


class _ContextFunction(_ContextObject):
    def _register(self):
        django_jinja.library.global_function(
            name=self.name,
            fn=jinja2.contextfunction(self))


class PriceDisplayFilter(_ContextFilter):
    def __call__(self, context, item, quantity=1, include_taxes=None, allow_cache=True):
        options = PriceDisplayOptions.from_context(context)
        if options.hide_prices:
            return ""

        if include_taxes is None:
            include_taxes = options.include_taxes

        request = context.get('request')
        orig_priceful = _get_priceful(request, item, quantity)
        if not orig_priceful:
            return ""

        priceful = convert_taxness(request, item, orig_priceful, include_taxes)
        return money(getattr(priceful, self.property_name))


class PricePropertyFilter(_ContextFilter):
    def __call__(self, context, item, quantity=1, allow_cache=True):
        priceful = _get_priceful(context.get('request'), item, quantity)
        if not priceful:
            return ""

        return getattr(priceful, self.property_name)


class PricePercentPropertyFilter(_ContextFilter):
    def __call__(self, context, item, quantity=1, allow_cache=True):
        priceful = _get_priceful(context.get('request'), item, quantity)
        if not priceful:
            return ""

        return percent(getattr(priceful, self.property_name))


class TotalPriceDisplayFilter(_ContextFilter):
    def __call__(self, context, source, include_taxes=None):
        """
        :type source: shuup.core.order_creator.OrderSource|
                      shuup.core.models.Order
        """
        options = PriceDisplayOptions.from_context(context)
        if options.hide_prices:
            return ""
        if include_taxes is None:
            include_taxes = options.include_taxes
        try:
            if include_taxes is None:
                total = source.total_price
            elif include_taxes:
                total = source.taxful_total_price
            else:
                total = source.taxless_total_price
        except TypeError:
            total = source.total_price
        return money(total)


class PriceRangeDisplayFilter(_ContextFilter):
    def __call__(self, context, product, quantity=1, allow_cache=True):
        """
        :type product: shuup.core.models.Product
        """
        options = PriceDisplayOptions.from_context(context)
        if options.hide_prices:
            return ("", "")

        request = context.get('request')
        priced_children_key = PRICED_CHILDREN_CACHE_KEY % (product.id, quantity)
        if hasattr(request, priced_children_key):
            priced_children = getattr(request, priced_children_key)
        else:
            priced_children = product.get_priced_children(request, quantity)
            setattr(request, priced_children_key, priced_children)
        priced_products = priced_children if priced_children else [
            (product, _get_priceful(request, product, quantity))]

        def get_formatted_price(priced_product):
            (prod, price_info) = priced_product
            if not price_info:
                return ""
            pf = convert_taxness(request, prod, price_info, options.include_taxes)
            price = money(pf.price)
            return price

        min_max = (priced_products[0], priced_products[-1])
        return tuple(get_formatted_price(x) for x in min_max)


def _get_priceful(request, item, quantity):
    """
    Get priceful from given item.

    If item has `get_price_info` method, it will be called with given
    `request` and `quantity` as arguments, otherwise the item itself
    should implement the `Priceful` interface.

    :type request: django.http.HttpRequest
    :type item: shuup.core.taxing.TaxableItem
    :type quantity: numbers.Number
    :rtype: shuup.core.pricing.Priceful|None
    """
    if hasattr(item, 'get_price_info'):
        key_prefix = "%s-%s-" % (item.id, quantity)
        price_key = "%s_get_priceful" % key_prefix
        if hasattr(request, price_key):
            return getattr(request, price_key)

        if hasattr(item, 'is_variation_parent') and item.is_variation_parent():
            priced_children_key = PRICED_CHILDREN_CACHE_KEY % (item.id, quantity)
            priced_children = getattr(request, priced_children_key, None)
            if priced_children is None:
                priced_children = item.get_priced_children(request, quantity)
                setattr(request, priced_children_key, priced_children)
            price = (priced_children[0][1] if priced_children
                     else item.get_cheapest_child_price_info(request, quantity))
        else:
            price = item.get_price_info(request, quantity=quantity)
        setattr(request, price_key, price)
        return price
    if hasattr(item, 'get_total_cost'):
        return item.get_total_cost(request.basket)

    assert isinstance(item, Priceful)
    return item
