# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _

from shoop.core import taxing
from shoop.core.pricing import TaxfulPrice, TaxlessPrice
from shoop.core.taxing._context import TaxingContext
from shoop.core.taxing.utils import stacked_value_added_taxes
from shoop.default_tax.models import TaxRule
from shoop.utils.iterables import first


class DefaultTaxModule(taxing.TaxModule):
    identifier = "default_tax"
    name = _("Default Taxation")

    def determine_product_tax(self, context, product):
        """
        :type context: shoop.core.contexts.PriceTaxContext
        :type product: shoop.core.models.Product
        """
        price = product.get_price(context)
        return _calculate_taxes(
            price,
            taxing_context=context.taxing_context,
            tax_class=product.tax_class,
        )

    def get_line_taxes(self, source_line):
        """
        :type source_line: shoop.core.order_creator.SourceLine
        :rtype: Iterable[LineTax]
        """
        taxing_context = TaxingContext(
            customer_tax_group=_resolve(source_line, 'source.customer.tax_group'),
            location=_resolve(source_line, 'source.billing_address'),
        )
        return _calculate_taxes(
            source_line.total_price,
            taxing_context=taxing_context,
            tax_class=source_line.get_tax_class(),
        ).taxes


def _calculate_taxes(price, taxing_context, tax_class):
    customer_tax_group = taxing_context.customer_tax_group
    # Check tax exempt
    # TODO: Should this be done in some better way?
    if customer_tax_group and customer_tax_group.identifier == 'tax_exempt':
        return taxing.TaxedPrice(
            TaxfulPrice(price.amount), TaxlessPrice(price.amount), []
        )

    tax_rules = TaxRule.objects.filter(enabled=True, tax_classes=tax_class)
    if customer_tax_group:
        tax_rules = tax_rules.filter(customer_tax_groups=customer_tax_group)
    tax_rules = tax_rules.order_by("-priority")  # TODO: Do the Right Thing with priority
    taxes = [tax_rule for tax_rule in tax_rules if tax_rule.matches(taxing_context)]
    tax_rule = first(taxes)  # TODO: Do something better than just using the first tax!
    tax = getattr(tax_rule, "tax", None)
    return stacked_value_added_taxes(price, [tax] if tax else [])


def _resolve(obj, path):
    for name in path.split('.'):
        obj = getattr(obj, name, None)
    return obj
