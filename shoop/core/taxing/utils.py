# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from shoop.core.pricing import TaxfulPrice, TaxlessPrice

from ._line_tax import SourceLineTax
from ._price import TaxedPrice


def stacked_value_added_taxes(price, taxes):
    """
    Stack value-added taxes on the given price without compounding.

    Note that this will not take compound taxation (Quebec) into account.

    :param price: Price
    :type price: shoop.core.pricing.Price
    :param taxes: List of Tax objects
    :type taxes: list[shoop.core.models.Tax]
    :return: TaxedPrice with the calculated taxes.
    :rtype: TaxedPrice
    """
    if not taxes:
        return TaxedPrice(TaxfulPrice(price), TaxlessPrice(price))

    taxful = None

    if price.includes_tax:
        taxful = price
        rate_sum = sum(tax.rate for tax in taxes if tax.rate)
        amount_sum = sum(tax.amount for tax in taxes if tax.amount)
        taxless = TaxlessPrice((taxful.amount - amount_sum) / (1 + rate_sum))
    else:
        taxless = price

    line_taxes = [
        SourceLineTax(
            tax=tax,
            name=tax.name,
            amount=tax.calculate_amount(taxless.amount),
            base_amount=taxless.amount,
        )
        for tax in taxes
    ]

    if taxful is None:
        taxful = TaxfulPrice(taxless.amount + sum(lt.amount for lt in line_taxes))

    return TaxedPrice(taxful, taxless, line_taxes)
