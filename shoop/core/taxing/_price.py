# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.core.pricing import TaxfulPrice, TaxlessPrice


class TaxedPrice(object):
    def __init__(self, taxful, taxless, taxes=None):
        """
        Initialize from given prices and taxes.

        :type taxful: shoop.core.pricing.TaxfulPrice
        :type taxless: shoop.core.pricing.TaxlessPrice
        :type taxes: list[LineTax]|None
        """
        assert isinstance(taxful, TaxfulPrice)
        assert isinstance(taxless, TaxlessPrice)
        if not taxes:
            taxes = ()
        self.taxful = taxful
        self.taxless = taxless
        self.taxes = taxes
        assert not taxes or (
            taxful.amount == (taxless.amount + sum(x.amount for x in taxes))
        )

    @property
    def tax_rate(self):
        return (self.taxful.amount / self.taxless.amount) - 1
