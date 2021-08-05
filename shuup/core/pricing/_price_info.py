# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import numbers

from ._price import Price
from ._priceful import Priceful


class PriceInfo(Priceful):
    """
    Object for passing around pricing data of an item.
    """

    price = None
    base_price = None
    quantity = None
    expires_on = None

    def __init__(self, price, base_price, quantity, expires_on=None):
        """
        Initialize PriceInfo with prices and other parameters.

        Prices can be taxful or taxless, but their types must match.

        :type price: Price
        :param price:
          Effective price for the specified quantity.
        :type base_price: Price
        :param base_price:
          Base price for the specified quantity.  Discounts are
          calculated based on this.
        :type quantity: numbers.Number
        :param quantity:
          Quantity that the given price is for.  Unit price is
          calculated by ``discounted_unit_price = price / quantity``.
          Note: Quantity could be non-integral (i.e. decimal).
        :type expires_on: numbers.Number|None
        :param expires_on:
          Unix timestamp, comparable to values returned by :func:`time.time`,
          determining the point in time when the prices are no longer
          valid, or None if no expire time is set (which could mean
          indefinitely, but in reality, it just means undefined).
        """
        assert isinstance(price, Price)
        assert isinstance(base_price, Price)
        assert price.unit_matches_with(base_price)
        assert isinstance(quantity, numbers.Number)
        assert expires_on is None or isinstance(expires_on, numbers.Number)

        self.price = price
        self.base_price = base_price
        self.quantity = quantity
        self.expires_on = expires_on

    def __lt__(self, other):
        return self.price.value < other.price.value

    def __le__(self, other):
        return self.price.value <= other.price.value

    def __gt__(self, other):
        return self.price.value > other.price.value

    def __ge__(self, other):
        return self.price.value >= other.price.value

    def __eq__(self, other):
        return self.price.value == other.price.value

    def __ne__(self, other):
        return self.price.value != other.price.value

    def __repr__(self):
        expire_str = "" if self.expires_on is None else (", expires_on=%r" % (self.expires_on,))
        return "%s(%r, %r, %r%s)" % (type(self).__name__, self.price, self.base_price, self.quantity, expire_str)
