# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
"""
Shuup modular product pricing functionality.

The pricing module in use is declared by the
:obj:`~shuup.core.settings.SHUUP_PRICING_MODULE` setting.  The
default is a pricing module that always prices everything to be free.
The base distribution contains :obj:`shuup.customer_group_pricing`, which is an
useful pricing module for many cases.

To acquire an instance of the current pricing module, use
:func:`get_pricing_module`.

In brief, a pricing module is able to price a product based on a
*context*; what exactly a context contains is determined by the module
in question.  You can construct a context from a request by calling the
module's :func:`~PricingModule.get_context_from_request` method, or
for more advanced uses, when you do not have access to an HTTP request,
:func:`~PricingModule.get_context_from_data`.

After you have acquired the module and a context, you can calculate
prices for a product with the module's
:func:`~PricingModule.get_price_info` method.
(:class:`~shuup.core.models.Product` objects contain the
convenience methods
:func:`~shuup.core.models.Product.get_price_info`,
:func:`~shuup.core.models.Product.get_price`,
and :func:`~shuup.core.models.Product.get_base_price`
which do these steps for you.)

If you have multiple products, it will likely be more efficient --
depending on the implementation of the module -- to use the
:func:`~PricingModule.get_price_infos` method.

TODO: document the concepts of base price and the pricing steps API.
TODO: caching.
"""

from __future__ import unicode_literals

from shuup.utils import update_module_attributes

from ._context import PricingContext, PricingContextable
from ._discounts import DiscountModule, get_discount_modules
from ._module import get_pricing_module, PricingModule
from ._price import Price, TaxfulPrice, TaxlessPrice
from ._price_display_options import PriceDisplayOptions
from ._price_info import PriceInfo
from ._priceful import Priceful
from ._utils import (
    get_price_info, get_price_infos, get_pricing_steps,
    get_pricing_steps_for_products
)

__all__ = [
    "DiscountModule",
    "get_discount_modules",
    "get_price_info",
    "get_price_infos",
    "get_pricing_module",
    "get_pricing_steps",
    "get_pricing_steps_for_products",
    "Price",
    "PriceDisplayOptions",
    "Priceful",
    "PriceInfo",
    "PricingContext",
    "PricingContextable",
    "PricingModule",
    "TaxfulPrice",
    "TaxlessPrice",
]

update_module_attributes(__all__, __name__)
