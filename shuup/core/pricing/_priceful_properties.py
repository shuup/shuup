# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from ._price import TaxfulPrice, TaxlessPrice


class PriceRate(object):
    doc_prefix = ""

    def __init__(self, price_field):
        self.price_field = price_field
        self.__doc__ = "%s `%s`" % (self.doc_prefix, price_field)

    def __get__(self, instance, type=None):
        """
        :rtype: shuup.core.pricing.Price
        """
        if instance is None:
            return self
        taxful = instance.raw_taxful_price
        taxless = instance.raw_taxless_price
        price = getattr(instance, self.price_field)
        return self._convert(taxful, taxless, price)


class TaxfulFrom(PriceRate):
    doc_prefix = "Taxful"

    def _convert(self, taxful, taxless, price):
        """
        :rtype: TaxfulPrice
        """
        if price.includes_tax:
            return price
        else:
            tax_ratio = taxful.value / taxless.value if taxless else 1
            return TaxfulPrice(price.amount * tax_ratio)


class TaxlessFrom(PriceRate):
    doc_prefix = "Taxless"

    def _convert(self, taxful, taxless, price):
        """
        :rtype: TaxlessPrice
        """
        if price.includes_tax:
            inv_tax_ratio = taxless.value / taxful.value if taxful else 1
            return TaxlessPrice(price.amount * inv_tax_ratio)
        else:
            return price
