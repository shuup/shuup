# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from shoop.core import taxing
from shoop.core.pricing import TaxfulPrice, TaxlessPrice
from shoop.core.taxing.utils import stacked_value_added_taxes
from shoop.default_tax.models import TaxRule
from shoop.utils.iterables import first


class DefaultTaxModule(taxing.TaxModule):
    identifier = "default_tax"
    name = _("Default Taxation")

    def get_taxed_price_for(self, context, item, price):
        return _calculate_taxes(price, context, item.tax_class)


def _calculate_taxes(price, taxing_context, tax_class):
    customer_tax_group = taxing_context.customer_tax_group
    # TODO: (TAX) Should tax exempt be done in some better way?
    if customer_tax_group and customer_tax_group.identifier == 'tax_exempt':
        return taxing.TaxedPrice(
            TaxfulPrice(price.amount), TaxlessPrice(price.amount), [])

    tax_rules = TaxRule.objects.filter(enabled=True, tax_classes=tax_class)
    if customer_tax_group:
        tax_rules = tax_rules.filter(
            Q(customer_tax_groups=customer_tax_group) |
            Q(customer_tax_groups=None))
    tax_rules = tax_rules.order_by("-priority")  # TODO: (TAX) Do the Right Thing with priority
    taxes = [tax_rule for tax_rule in tax_rules if tax_rule.matches(taxing_context)]
    tax_rule = first(taxes)  # TODO: (TAX) Do something better than just using the first tax!
    tax = getattr(tax_rule, "tax", None)
    return stacked_value_added_taxes(price, [tax] if tax else [])
