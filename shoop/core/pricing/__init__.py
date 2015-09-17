# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
"""
Shoop modular product pricing functionality.

The pricing module in use is declared by the
:obj:`~shoop.core.settings.SHOOP_PRICING_MODULE` setting.  The
default is a pricing module that always prices everything to be free.
The base distribution contains :obj:`shoop.simple_pricing`, which is an
useful pricing module for many cases.

To acquire an instance of the current pricing module, use
:func:`get_pricing_module`.

In brief, a pricing module is able to price a product based on a
*context*; what exactly a context contains is determined by the module
in question.  You can construct a context from a request by calling the
module's :func:`~PricingModule.get_context_from_request` method, or
for more advanced uses, when you do not have access to an HTTP request,
:func:`~PricingModule.get_context_from_data`.

After you have acquired the module and a context, you can calculate
prices for a product with the module's
:func:`~PricingModule.get_price_info` method.
(:class:`~shoop.core.models.products.Product` objects contain the
convenience methods
:func:`~shoop.core.models.products.Product.get_price_info`,
:func:`~shoop.core.models.products.Product.get_price`,
and :func:`~shoop.core.models.products.Product.get_base_price`
which do these steps for you.)

If you have multiple products, it will likely be more efficient --
depending on the implementation of the module -- to use the
:func:`~PricingModule.get_price_infos` method.

TODO: document the concepts of base price and the pricing steps API.
TODO: caching.
"""

from __future__ import unicode_literals
import abc
import six

import hashlib
from shoop.apps.provides import load_module
from django.http import HttpRequest
from django.utils.encoding import force_bytes
from django.utils.timezone import now

from .price import Price, TaxfulPrice, TaxlessPrice
from .price_info import PriceInfo

__all__ = [
    "Price",
    "PriceInfo",
    "PricingContext",
    "PricingModule",
    "TaxfulPrice",
    "TaxlessPrice",
    "get_pricing_module",
]


def get_pricing_module():
    """
    :rtype: shoop.core.pricing.PricingModule
    """
    return load_module("SHOOP_PRICING_MODULE", "pricing_module")()


class PricingContext(object):
    REQUIRED_VALUES = ()

    def __init__(self, **kwargs):
        kwargs.setdefault("time", now())
        for name, value in kwargs.items():
            setattr(self, name, value)
        for name in self.REQUIRED_VALUES:
            if not hasattr(self, name):
                raise ValueError("%s is a required value for %s but is not set." % (name, self))

    def get_cache_key_parts(self):
        return [getattr(self, key) for key in self.REQUIRED_VALUES]

    def get_cache_key(self):
        parts_text = "\n".join(force_bytes(part) for part in self.get_cache_key_parts())
        return "%s_%s" % (
            self.__class__.__name__,
            hashlib.sha1(parts_text).hexdigest()
        )

    cache_key = property(get_cache_key)


class PricingModule(six.with_metaclass(abc.ABCMeta)):
    identifier = None
    name = None
    pricing_context_class = PricingContext

    def get_context(self, context):
        """
        :rtype: PricingContext
        """
        if hasattr(context, "pricing_context"):
            context = context.pricing_context
        if isinstance(context, self.pricing_context_class):
            return context
        elif isinstance(context, HttpRequest):
            return self.get_context_from_request(context)
        else:
            return self.get_context_from_data(**(context or {}))

    def get_context_from_request(self, request):
        # This implementation does not use `request` at all.
        return self.pricing_context_class()

    def get_context_from_data(self, **context_data):
        return self.pricing_context_class(**context_data)

    @abc.abstractmethod
    def get_price_info(self, context, product, quantity=1):
        """
        :param product: `Product` object or id of `Product`
        :type product: shoop.core.models.Product|int
        :rtype: PriceInfo
        """
        pass

    def get_pricing_steps(self, context, product_id):
        """
        Get context-specific list pricing steps for the given product.

        Returns a list of tuples

        [(0, price0), (quantity1, price1), (quantity2, price2), ...]

        where price for 0 <= quantity < quantity1 is price0, and price
        for quantity1 <= quantity < quantity2 is price1, and so on.

        If there are "no steps", the return value will be a list of
        single step with the constant price, i.e. [(0, price)].

        :rtype: list[tuple[Decimal,Price]]
        """
        return [(0, TaxlessPrice(0))]

    def get_price_infos(self, context, products, quantity=1):
        """
        :param products: a list of `Product`s or id's
        :type products:  Iterable[shoop.core.models.Product|int]
        :rtype: dict[int,PriceInfo]
        """
        product_ids = [getattr(x, "pk", x) for x in products]
        return {
            product_id: self.get_price_info(context=context, product=product_id, quantity=quantity)
            for product_id in product_ids
        }

    def get_pricing_steps_for_products(self, context, products):
        product_ids = [getattr(x, "pk", x) for x in products]
        return {
            product_id: self.get_pricing_steps(context, product_id=product_id)
            for product_id in product_ids
        }
