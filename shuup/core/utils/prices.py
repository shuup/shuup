# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.core.pricing import PriceInfo
from shuup.core.taxing import get_tax_module, should_calculate_taxes_automatically


def convert_taxness(request, item, priceful, with_taxes):
    """
    Convert taxness of a priceful object.

    Return a `Priceful` object ``result`` satisfying
    ``result.price.includes_tax == with_taxes`` if possible.

    When given `priceful` does not have tax amount and taxes cannot be
    calculated automatically (`should_calculate_taxes_automatically`
    returns false), return the given `priceful` as is.

    Given `request` is used for constructing a
    `~shuup.core.taxing.TaxingContext`.

    :type request: django.http.HttpRequest
    :type item: shuup.core.taxing.TaxableItem
    :type priceful: shuup.core.pricing.Priceful
    :type with_taxes: bool|None
    :rtype: shuup.core.pricing.Priceful
    """
    if with_taxes is None or priceful.price.includes_tax == with_taxes:
        return priceful

    taxed_priceful = _make_taxed(request, item, priceful, with_taxes)

    return taxed_priceful if taxed_priceful else priceful


def _make_taxed(request, item, priceful, with_taxes):
    """
    :type request: django.http.HttpRequest
    :type item: shuup.core.taxing.TaxableItem
    :type priceful: shuup.core.pricing.Priceful
    :rtype: shuup.core.pricing.Priceful|None
    """
    try:
        tax_amount = getattr(priceful, "tax_amount", None)
    except TypeError:  # e.g. shuup.core.order_creator.TaxesNotCalculated
        tax_amount = None

    if tax_amount is not None:
        if with_taxes:
            return TaxedPriceInfo(
                priceful.taxful_price, priceful.taxful_base_price, quantity=priceful.quantity, tax_amount=tax_amount
            )
        else:
            return TaxedPriceInfo(
                priceful.taxless_price, priceful.taxless_base_price, quantity=priceful.quantity, tax_amount=tax_amount
            )

    if not should_calculate_taxes_automatically():
        return None

    taxmod = get_tax_module()
    taxctx = taxmod.get_context_from_request(request)
    price = taxmod.get_taxed_price_for(taxctx, item, priceful.price)
    base_price = taxmod.get_taxed_price_for(taxctx, item, priceful.base_price)

    if with_taxes:
        return TaxedPriceInfo(price.taxful, base_price.taxful, quantity=priceful.quantity, tax_amount=price.tax_amount)
    else:
        return TaxedPriceInfo(
            price.taxless, base_price.taxless, quantity=priceful.quantity, tax_amount=price.tax_amount
        )


class TaxedPriceInfo(PriceInfo):
    def __init__(self, price, base_price, quantity, tax_amount, **kwargs):
        super(TaxedPriceInfo, self).__init__(price, base_price, quantity, **kwargs)
        self.tax_amount = tax_amount
