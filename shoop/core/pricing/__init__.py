# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
"""
Shoop modular product pricing functionality.

The pricing module in use is declared by the
:obj:`~shoop.core.settings.SHOOP_PRICING_MODULE` setting.  The
default is a pricing module that always prices everything to be free.
The base distribution contains :obj:`shoop.simple_pricing`, which is an
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
(:class:`~shoop.core.models.Product` objects contain the
convenience methods
:func:`~shoop.core.models.Product.get_price_info`,
:func:`~shoop.core.models.Product.get_price`,
and :func:`~shoop.core.models.Product.get_base_price`
which do these steps for you.)

If you have multiple products, it will likely be more efficient --
depending on the implementation of the module -- to use the
:func:`~PricingModule.get_price_infos` method.

TODO: document the concepts of base price and the pricing steps API.
TODO: caching.
"""

from __future__ import unicode_literals

from shoop.utils import update_module_attributes

from ._context import PricingContext, PricingContextable
from ._module import get_pricing_module, PricingModule
from ._price import Price, TaxfulPrice, TaxlessPrice
from ._price_info import PriceInfo
from ._priceful import Priceful

__all__ = [
    "Price",
    "Priceful",
    "PriceInfo",
    "PricingContext",
    "PricingContextable",
    "PricingModule",
    "TaxfulPrice",
    "TaxlessPrice",
    "get_pricing_module",
]

update_module_attributes(__all__, __name__)
