# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from shoop.core.pricing import TaxfulPrice, TaxlessPrice
from shoop.utils.money import Money

from ._line_tax import SourceLineTax
from ._price import TaxedPrice


def stacked_value_added_taxes(price, taxes):
    """
    Stack value-added taxes on the given price without compounding.

    Note that this will not take compound taxation (Quebec) into account.

    :param price: Taxful or taxless price to calculate taxes for
    :type price: shoop.core.pricing.Price
    :param taxes: List of Tax objects
    :type taxes: list[shoop.core.models.Tax]
    :return: TaxedPrice with the calculated taxes.
    :rtype: TaxedPrice
    """
    def money_sum(iterable):
        return sum(iterable, Money(0, price.currency))

    if not taxes:
        return TaxedPrice(TaxfulPrice(price), TaxlessPrice(price), [])

    if price.includes_tax:
        taxful = price
        rate_sum = sum(tax.rate for tax in taxes if tax.rate)
        amount_sum = money_sum(tax.amount for tax in taxes if tax.amount)
        taxless = TaxlessPrice((taxful.amount - amount_sum) / (1 + rate_sum))
    else:
        taxful = None  # will be calculated below
        taxless = price

    line_taxes = [
        SourceLineTax.from_tax(tax=tax, base_amount=taxless.amount)
        for tax in taxes
    ]

    if taxful is None:
        total_tax_amount = money_sum(x.amount for x in line_taxes)
        taxful = TaxfulPrice(taxless.amount + total_tax_amount)

    return TaxedPrice(taxful, taxless, line_taxes)
