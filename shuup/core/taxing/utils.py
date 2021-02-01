# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from collections import defaultdict

from shuup.core.pricing import TaxfulPrice, TaxlessPrice
from shuup.utils.money import Money

from ._line_tax import SourceLineTax
from ._price import TaxedPrice


def get_tax_class_proportions(lines):
    """
    Generate tax class proportions from taxed lines.

    Sum prices per tax class and return a list of (tax_class, factor)
    pairs, where factor is the proportion of total price of lines with
    given tax class from the total price of all lines.

    :type lines: list[shuup.core.order_creator.SourceLine]
    :param lines: List of taxed lines to generate proportions from
    :rtype: list[(shuup.core.models.TaxClass, decimal.Decimal)]
    :return:
      List of tax classes with a proportion, or empty list if total
      price is zero.  Sum of proportions is 1.
    """
    if not lines:
        return []

    zero = lines[0].price.new(0)

    total_by_tax_class = defaultdict(lambda: zero)
    total = zero

    for line in lines:
        total_by_tax_class[line.tax_class] += line.price
        total += line.price

    if not total:
        # Can't calculate proportions, if total is zero
        return []

    return [
        (tax_class, tax_class_total / total)
        for (tax_class, tax_class_total) in total_by_tax_class.items()
    ]


def stacked_value_added_taxes(price, taxes):
    """
    Stack added taxes on the given price without compounding.

    Note that this will not take compound taxation (Quebec) into account.

    :param price: Taxful or taxless price to calculate taxes for
    :type price: shuup.core.pricing.Price
    :param taxes: List of Tax objects
    :type taxes: list[shuup.core.models.Tax]
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


def calculate_compounded_added_taxes(price, tax_groups):
    """
    Calculate compounded and added taxes from given groups of taxes.

    The `tax_groups` argument should be a list of tax groups, where each
    tax group is a list of `Tax` objects.  Taxes in each tax group will
    be added together and finally each added tax group will be
    compounded over each other.

    :param price: Taxful or taxless price to calculate taxes for
    :type price: shuup.core.pricing.Price
    :param tax_groups: List of tax groups, each being a list of taxes
    :type tax_groups: list[list[shuup.core.models.Tax]]
    :return: TaxedPrice with the calculated taxes.
    :rtype: TaxedPrice
    """
    if price.includes_tax:
        return _calc_compounded_added_taxes_from_taxful(price, tax_groups)
    else:
        return _calc_compounded_added_taxes_from_taxless(price, tax_groups)


def _calc_compounded_added_taxes_from_taxful(amount, tax_groups):
    base_price = TaxfulPrice(amount)
    reversed_line_taxes = []
    for taxes in reversed(tax_groups):
        taxed_price = stacked_value_added_taxes(base_price, taxes)
        base_price = TaxfulPrice(taxed_price.taxless)
        reversed_line_taxes.extend(reversed(taxed_price.taxes))
    line_taxes = list(reversed(reversed_line_taxes))
    return TaxedPrice(
        taxful=TaxfulPrice(amount),
        taxless=TaxlessPrice(base_price),
        taxes=line_taxes)


def _calc_compounded_added_taxes_from_taxless(amount, tax_groups):
    base_price = TaxlessPrice(amount)
    line_taxes = []
    for taxes in tax_groups:
        taxed_price = stacked_value_added_taxes(base_price, taxes)
        base_price = TaxlessPrice(taxed_price.taxful)
        line_taxes.extend(taxed_price.taxes)
    return TaxedPrice(
        taxful=TaxfulPrice(base_price),
        taxless=TaxlessPrice(amount),
        taxes=line_taxes)
