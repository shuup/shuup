# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
"""
Template tags for displaying prices correctly.

Prefer these filters for rendering prices of products and basket lines
or total price of basket, since the will take price display options of
current template context into account (see `PriceDisplayOptions`).
Especially, they convert prices to correct taxness.

There is also a global context function `show_prices` which can be used
to render certain price container elements conditionally.
"""

import django_jinja
import jinja2

from shuup.core.utils.price_display import (
    PriceDisplayFilter, PriceDisplayOptions, PricePercentPropertyFilter,
    PricePropertyFilter, PriceRangeDisplayFilter, TotalPriceDisplayFilter
)

# Filters for Product, SourceLine, BasketLine, OrderLine, Service

price = PriceDisplayFilter('price')
base_price = PriceDisplayFilter('base_price')
base_unit_price = PriceDisplayFilter('base_unit_price')
discount_amount = PriceDisplayFilter('discount_amount')
discounted_unit_price = PriceDisplayFilter('discounted_unit_price')
unit_discount_amount = PriceDisplayFilter('unit_discount_amount')
is_discounted = PricePropertyFilter('is_discounted')
discount_percent = PricePercentPropertyFilter('discount_percent', 'discount_rate')
tax_percent = PricePercentPropertyFilter('tax_percent', 'tax_rate')
discount_rate = PricePropertyFilter('discount_rate')
tax_rate = PricePropertyFilter('tax_rate')

# Filters for Product

price_range = PriceRangeDisplayFilter('price_range')

# Filters for OrderSource, BaseBasket, Order

total_price = TotalPriceDisplayFilter('total_price')


@django_jinja.library.global_function
@jinja2.contextfunction
def show_prices(context):
    """
    Return true if price display options has show prices enabled.

    :type context: jinja2.runtime.Context
    """
    options = PriceDisplayOptions.from_context(context)
    return options.show_prices
