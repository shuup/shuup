# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import decimal

from shoop.core.pricing import TaxfulPrice, TaxlessPrice


class Priceful(object):
    """
    Define line price properties by others.

    Needs quantity, base_unit_price, total_discount and total_tax_amount
    properties.

    The base_unit_price, total_discount and total_tax_amount must have
    compatible units (taxness and currency).

    Invariants (excluding type conversions):
      * total_price = base_unit_price * quantity - total_discount
      * taxful_total_price = taxless_total_price + total_tax_amount
      * tax_rate = (taxful_total_price / taxless_total_price) - 1
      * tax_percentage = 100 * tax_rate
    """
    @property
    def total_price(self):
        """
        :rtype: shoop.core.pricing.Price
        """
        return self.base_unit_price * self.quantity - self.total_discount

    @property
    def taxful_total_price(self):
        """
        :rtype: TaxfulPrice
        """
        total = self.total_price
        if total.includes_tax:
            return total
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
            return total

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
    def tax_percentage(self):
        """
        :rtype: decimal.Decimal
        """
        return self.tax_rate * 100

    @property
    def taxful_base_unit_price(self):
        return self._make_taxful(self.base_unit_price)

    @property
    def taxless_base_unit_price(self):
        return self._make_taxless(self.base_unit_price)

    @property
    def taxful_total_discount(self):
        return self._make_taxful(self.total_discount)

    @property
    def taxless_total_discount(self):
        return self._make_taxless(self.total_discount)

    @property
    def discounted_unit_price(self):
        if not self.quantity:
            return self.base_unit_price
        return self.base_unit_price - (self.total_discount / self.quantity)

    @property
    def taxful_discounted_unit_price(self):
        return self._make_taxful(self.discounted_unit_price)

    @property
    def taxless_discounted_unit_price(self):
        return self._make_taxless(self.discounted_unit_price)

    def _make_taxful(self, price):
        """
        :rtype: TaxfulPrice
        """
        if price.includes_tax:
            return price
        else:
            return TaxfulPrice(price.amount * (1 + self.tax_rate))

    def _make_taxless(self, price):
        """
        :rtype: TaxlessPrice
        """
        if price.includes_tax:
            return TaxlessPrice(price.amount / (1 + self.tax_rate))
        else:
            return price
