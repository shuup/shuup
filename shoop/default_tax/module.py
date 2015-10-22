# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from itertools import groupby
from operator import attrgetter

from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from shoop.core import taxing
from shoop.core.taxing.utils import calculate_compounded_added_taxes
from shoop.default_tax.models import TaxRule
from shoop.utils.iterables import first


class DefaultTaxModule(taxing.TaxModule):
    identifier = "default_tax"
    name = _("Default Taxation")

    def get_taxed_price_for(self, context, item, price):
        return _calculate_taxes(price, context, item.tax_class)


def _calculate_taxes(price, taxing_context, tax_class):
    rules = _get_enabled_tax_rules(taxing_context, tax_class)
    tax_groups = get_taxes_of_effective_rules(taxing_context, rules)
    return calculate_compounded_added_taxes(price, tax_groups)


def _get_enabled_tax_rules(taxing_context, tax_class):
    """
    Get enabled tax rules from the db for given parameters.

    Returned rules are ordered desceding by override group and then
    ascending by priority (as required by `_filter_and_group_rules`).

    :type taxing_context: shoop.core.taxing.TaxingContext
    :type tax_class: shoop.core.models.TaxClass
    """
    tax_rules = TaxRule.objects.filter(enabled=True, tax_classes=tax_class)
    if taxing_context.customer_tax_group:
        tax_rules = tax_rules.filter(
            Q(customer_tax_groups=taxing_context.customer_tax_group) |
            Q(customer_tax_groups=None))
    tax_rules = tax_rules.order_by('-override_group', 'priority')
    return tax_rules


def get_taxes_of_effective_rules(taxing_context, tax_rules):
    """
    Get taxes grouped by priority from effective tax rules.

    Effective tax rules is determined by first limiting the scope to the
    rules that match the given taxing context (see `TaxRule.match`) and
    then further limiting the matching rules by selecting only the rules
    in the highest numbered override group.

    The `Tax` objects in the effective rules will be grouped by the
    priority of the rules.  The tax groups are returned as list of tax
    lists.

    :type taxing_context: shoop.core.taxing.TaxingContext
    :param tax_rules:
      Tax rules to filter from.  These should be ordered desceding by
      override group and then ascending by priority.
    :type tax_rules: Iterable[TaxRule]
    :rtype: list[list[shoop.core.models.Tax]]
    """
    # Limit our scope to only matching rules
    matching_rules = (
        tax_rule for tax_rule in tax_rules
        if tax_rule.matches(taxing_context))

    # Further limit our scope to the highest numbered override group
    grouped_by_override = groupby(matching_rules, attrgetter('override_group'))
    highest_override_group = first(grouped_by_override, (None, []))[1]

    # Group rules by priority
    grouped_rules = groupby(highest_override_group, attrgetter('priority'))
    tax_groups = [
        [rule.tax for rule in rules]
        for (_, rules) in grouped_rules]

    return tax_groups
