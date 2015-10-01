# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import decimal
import numbers

from shoop.core.pricing import Price


class PriceInfo(object):
    """
    Object for passing around pricing data of an item.
    """
    def __init__(self, price, base_price, quantity, expires_on=None):
        """
        Initialize PriceInfo with prices and other parameters.

        Prices can be taxful or taxless, but their types must match.

        :param Price price:
          Effective price for the specified quantity.
        :param Price base_price:
          Base price for the specified quantity.  Discounts are
          calculated based on this.
        :param numbers.Number quantity:
          Quantity that the given price is for.  Unit price is
          calculated by ``unit_price = price / quantity``.
          Note: Quantity could be non-integral (i.e. decimal).
        :param numbers.Number|None expires_on:
          Timestamp, comparable to values returned by :func:`time.time`,
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

    def __repr__(self):
        expire_str = '' if self.expires_on is None else(
            ', expires_on=%r' % (self.expires_on,))
        return "%s(%r, %r, %r%s)" % (
            type(self).__name__, self.price, self.base_price, self.quantity,
            expire_str)

    @property
    def discount_amount(self):
        """
        Amount of discount for the total quantity.

        :rtype: Price
        """
        return (self.base_price - self.price)

    @property
    def discount_percentage(self):
        """
        Discount percentage, 100 meaning totally discounted.

        Note: Could be negative, when base price is smaller than
        effective price.  Could also be greater than 100, when effective
        price is negative.

        If base price is 0, will return 0.

        :rtype: decimal.Decimal
        """
        if not self.base_price:
            return decimal.Decimal(0)
        return (1 - (self.price / self.base_price)) * 100

    @property
    def is_discounted(self):
        return (self.price < self.base_price)

    @property
    def unit_price(self):
        return self.price / self.quantity

    @property
    def base_unit_price(self):
        return self.base_price / self.quantity

    @property
    def unit_discount_amount(self):
        return self.discount_amount / self.quantity
