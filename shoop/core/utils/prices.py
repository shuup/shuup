# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import decimal

from shoop.core.pricing import TaxfulPrice, TaxlessPrice


class LinePriceMixin(object):
    """
    Define line price properties by others.

    Needs quantity, unit_price, total_discount and total_tax_amount
    properties.

    The unit_price and total_discount must have compatible types.

    Invariant: total_price = unit_price * quantity - total_discount
    """
    @property
    def total_price(self):
        """
        :rtype: Price
        """
        return self.unit_price * self.quantity - self.total_discount

    @property
    def taxful_total_price(self):
        """
        :rtype: TaxfulPrice
        """
        total = self.total_price
        if total.includes_tax:
            return TaxfulPrice(total.amount)
        else:
            return TaxfulPrice(total.amount + self.total_tax_amount)

    @property
    def taxless_total_price(self):
        """
        :rtype: TaxlessPrice
        """
        total = self.total_price
        if total.includes_tax:
            return TaxlessPrice(total.amount - self.total_tax_amount)
        else:
            return TaxlessPrice(total.amount)

    @property
    def tax_rate(self):
        """
        :rtype: decimal.Decimal
        """
        taxless_total = self.taxless_total_price
        taxful_total = self.taxful_total_price
        if not taxless_total.amount:
            return decimal.Decimal(0)
        return (taxful_total.amount / taxless_total.amount) - 1

    @property
    def taxful_unit_price(self):
        """
        :rtype: TaxfulPrice
        """
        if self.unit_price.includes_tax:
            return self.unit_price
        else:
            return TaxfulPrice(self.unit_price.amount * (1 + self.tax_rate))

    @property
    def taxless_unit_price(self):
        """
        :rtype: TaxlessPrice
        """
        if self.unit_price.includes_tax:
            return TaxlessPrice(self.unit_price.amount / (1 + self.tax_rate))
        else:
            return self.unit_price

    @property
    def taxful_total_discount(self):
        """
        :rtype: TaxfulPrice
        """
        if self.total_discount.includes_tax:
            return self.total_discount
        else:
            return TaxfulPrice(self.total_discount.amount * (1 + self.tax_rate))

    @property
    def taxless_total_discount(self):
        """
        :rtype: TaxlessPrice
        """
        if self.total_discount.includes_tax:
            return TaxlessPrice(self.total_discount.amount / (1 + self.tax_rate))
        else:
            return self.total_discount
