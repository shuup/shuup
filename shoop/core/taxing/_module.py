# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.http import HttpRequest

from shoop.apps.provides import load_module
from shoop.core.pricing import TaxfulPrice, TaxlessPrice

from ._context import TaxingContext
from ._price import TaxedPrice


def get_tax_module():
    """
    Get the TaxModule specified in settings.

    :rtype: shoop.core.taxing.TaxModule
    """
    return load_module("SHOOP_TAX_MODULE", "tax_module")()


class TaxModule(object):
    identifier = None
    name = None

    taxing_context_class = TaxingContext

    def get_context(self, context):
        """
        :rtype: TaxingContext
        """
        if isinstance(context, self.taxing_context_class):
            return context
        elif isinstance(context, HttpRequest):
            return self.get_context_from_request(context)
        else:
            return self.get_context_from_data(**(context or {}))

    def get_context_from_request(self, request):
        # This implementation does not use `request` at all.
        return self.taxing_context_class()

    def get_context_from_data(self, **context_data):
        return self.taxing_context_class(**context_data)

    def determine_product_tax(self, context, product):
        """
        Determine taxes of product in given price-tax context.

        :type context: shoop.core.contexts.PriceTaxContext
        :type product: shoop.core.models.Product
        :rtype: TaxedPrice
        """
        # TODO: (TAX) Implement determine_product_tax (here or in subclass)
        # Default implementation considers everything taxless.

        price = product.get_price(context)
        return TaxedPrice(
            TaxfulPrice(price.amount),
            TaxlessPrice(price.amount)
        )

    # TODO: (TAX) Remove get_method_tax_amount? (Not needed probably)
    # def get_method_tax_amount(self, tax_view, method):
    #     pass

    def get_line_taxes(self, source_line):
        """
        Get taxes for given source line of an order source.

        :type source_line: shoop.core.order_creator.SourceLine
        :rtype: Iterable[LineTax]
        """
        # TODO: (TAX) Implement get_line_taxes (here or in subclass)
