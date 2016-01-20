# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import abc

import six

from shoop.apps.provides import load_module

from ._context import TaxingContext


def get_tax_module():
    """
    Get the TaxModule specified in settings.

    :rtype: shoop.core.taxing.TaxModule
    """
    return load_module("SHOOP_TAX_MODULE", "tax_module")()


class TaxModule(six.with_metaclass(abc.ABCMeta)):
    """
    Module for calculating taxes.
    """
    identifier = None
    name = None

    taxing_context_class = TaxingContext

    def get_context_from_request(self, request):
        customer = getattr(request, "customer", None)
        return self.get_context_from_data(customer=customer)

    def get_context_from_data(self, **context_data):
        customer = context_data.get("customer")
        customer_tax_group = (
            context_data.get("customer_tax_group") or
            (customer.tax_group if customer else None))
        customer_tax_number = (
            context_data.get("customer_tax_number") or
            getattr(customer, "tax_number", None))
        location = (
            context_data.get("location") or
            context_data.get("shipping_address") or
            (customer.default_shipping_address if customer else None))
        return self.taxing_context_class(
            customer_tax_group=customer_tax_group,
            customer_tax_number=customer_tax_number,
            location=location,
        )

    def get_context_from_order_source(self, source):
        return self.get_context_from_data(
            customer=source.customer, location=source.shipping_address)

    def add_taxes(self, source, lines):
        """
        Add taxes to given OrderSource lines.

        Given lines are modified in-place, also new lines may be added
        (with ``lines.extend`` for example).  If there is any existing
        taxes for the `lines`, they are simply replaced.

        :type source: shoop.core.order_creator.OrderSource
        :param source: OrderSource of the lines
        :type lines: list[shoop.core.order_creator.SourceLine]
        :param lines: List of lines to add taxes for
        """
        context = self.get_context_from_order_source(source)
        for line in lines:
            assert line.source == source
            if not line.parent_line_id:
                line.taxes = self._get_line_taxes(context, line)

    def _get_line_taxes(self, context, line):
        """
        Get taxes for given source line of an order source.

        :type context: TaxingContext
        :type line: shoop.core.order_creator.SourceLine
        :rtype: Iterable[LineTax]
        """
        taxed_price = self.get_taxed_price_for(context, line, line.price)
        return taxed_price.taxes

    @abc.abstractmethod
    def get_taxed_price_for(self, context, item, price):
        """
        Get TaxedPrice for taxable item.

        Taxable items could be products (`~shoop.core.models.Product`),
        shipping and payment methods (`~shoop.core.models.Method`), and
        lines (`~shoop.core.order_creator.SourceLine`).

        :param context: Taxing context to calculate in
        :type context: TaxingContext
        :param item: Item to get taxes for
        :type item: shoop.core.taxing.TaxableItem
        :param price: Price (taxful or taxless) to calculate taxes for
        :type price: shoop.core.pricing.Price

        :rtype: shoop.core.taxing.TaxedPrice
        """
        pass
