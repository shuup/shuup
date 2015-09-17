# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from shoop.core.pricing import Price


class PriceInfo(object):
    def __init__(self, price, base_price, expires_on=None):
        """
        Initialize PriceInfo with two given Price objects.

        Given prices can be taxful or taxless, but their types must match.

        :param price: Price of the product that is calculated in the pricing module
        :type price: shoop.core.pricing.Price
        :param base_price: Base price of the product, discounts are calculated based on this.
        :type base_price: shoop.core.pricing.Price
        """

        assert isinstance(price, Price)
        assert isinstance(base_price, Price)
        assert price.unit_matches_with(base_price)
        self.price = price
        self.base_price = base_price
        self.expires_on = expires_on

    @property
    def includes_tax(self):
        return self.price.includes_tax

    @property
    def discount_amount(self):
        return (self.base_price - self.price)

    @property
    def discount_percentage(self):
        return (1 - (self.price / self.base_price)) * 100

    @property
    def is_discounted(self):
        return (self.price < self.base_price)
