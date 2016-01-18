# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import abc

import six
from django.http import HttpRequest

from shoop.apps.provides import load_module

from ._context import PricingContext


def get_pricing_module():
    """
    :rtype: shoop.core.pricing.PricingModule
    """
    return load_module("SHOOP_PRICING_MODULE", "pricing_module")()


class PricingModule(six.with_metaclass(abc.ABCMeta)):
    identifier = None
    name = None
    pricing_context_class = PricingContext

    def get_context(self, context):
        """
        Create pricing context from pricing contextable object.

        :type context: PricingContextable
        :rtype: PricingContext
        """
        if isinstance(context, self.pricing_context_class):
            return context
        elif isinstance(context, HttpRequest):
            return self.get_context_from_request(context)
        raise TypeError("Not pricing contextable: %r" % (context,))

    def get_context_from_request(self, request):
        """
        Create pricing context from HTTP request.

        This base class implementation does not use `request` at all.

        :type request: HttpRequest
        :rtype: PricingContext
        """
        return self.pricing_context_class()

    def get_context_from_data(self, **context_data):
        """
        Create pricing context from keyword arguments.

        :rtype: PricingContext
        """
        return self.pricing_context_class(**context_data)

    @abc.abstractmethod
    def get_price_info(self, context, product, quantity=1):
        """
        Get price info of product for given quantity.

        :param product: `Product` object or id of `Product`
        :type product: shoop.core.models.Product|int
        :rtype: PriceInfo
        """
        pass

    def get_pricing_steps(self, context, product):
        """
        Get context-specific list pricing steps for the given product.

        Returns a list of PriceInfos ``[pi0, pi1, pi2, ...]`` where each
        PriceInfo object is at the border unit price change: unit price
        for ``0 <= quantity < pi1.quantity1`` is
        ``pi0.discounted_unit_price``, and unit price for
        ``pi1.quantity <= quantity < pi2.quantity`` is
        ``pi1.discounted_unit_price``, and so on.

        If there are "no steps", the return value will be a list of single
        PriceInfo object with the constant price, i.e. ``[price_info]``.

        :param product: Product or product id
        :type product: shoop.core.models.Product|int
        :rtype: list[PriceInfo]
        """
        return [self.get_price_info(context, product, quantity=1)]

    def get_price_infos(self, context, products, quantity=1):
        """
        Get PriceInfo objects for a bunch of products.

        Returns a dict with product id as key and PriceInfo as value.

        May be faster than doing :func:`get_price_info` for each product
        separately, since inheriting class may override this.

        :param products: List of product objects or id's
        :type products:  Iterable[shoop.core.models.Product|int]
        :rtype: dict[int,PriceInfo]
        """
        product_ids = [getattr(x, "pk", x) for x in products]
        return {
            product_id: self.get_price_info(context=context, product=product_id, quantity=quantity)
            for product_id in product_ids
        }

    def get_pricing_steps_for_products(self, context, products):
        """
        Get pricing steps for a bunch of products.

        Returns a dict with product id as key and step data (as list of
        PriceInfos) as values.

        May be faster than doing :func:`get_pricing_steps` for each
        product separately, since inheriting class may override this.

        :param products: List of product objects or id's
        :type products:  Iterable[shoop.core.models.Product|int]
        :rtype: dict[int,list[PriceInfo]]
        """
        product_ids = [getattr(x, "pk", x) for x in products]
        return {
            product_id: self.get_pricing_steps(context, product_id=product_id)
            for product_id in product_ids
        }
