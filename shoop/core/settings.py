# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
"""
Settings of Shoop Core.

See :ref:`apps-settings` (in :obj:`shoop.apps`) for general information
about the Shoop settings system.  Especially, when inventing settings of
your own, the :ref:`apps-naming-settings` section is an important read.
"""


# TODO: Document SHOOP_HOME_LOCALE
SHOOP_HOME_LOCALE = "en"

#: TODO: Document SHOOP_HOME_CURRENCY
SHOOP_HOME_CURRENCY = "EUR"

#: TODO: Document SHOOP_ALLOW_ANONYMOUS_ORDERS
SHOOP_ALLOW_ANONYMOUS_ORDERS = True

#: TODO: Document SHOOP_ORDER_IDENTIFIER_METHOD
SHOOP_ORDER_IDENTIFIER_METHOD = "id"

#: TODO: Document SHOOP_REFERENCE_NUMBER_METHOD
SHOOP_REFERENCE_NUMBER_METHOD = 'unique'

#: TODO: Document SHOOP_REFERENCE_NUMBER_LENGTH
SHOOP_REFERENCE_NUMBER_LENGTH = 10

#: TODO: Document SHOOP_REFERENCE_NUMBER_PREFIX
SHOOP_REFERENCE_NUMBER_PREFIX = ""

#: The identifier of the pricing module to use for pricing products.
#:
#: Determines how product prices are calculated.  See
#: :obj:`shoop.core.pricing` for details.
SHOOP_PRICING_MODULE = "simple_pricing"

#: The identifier of the tax module to use for determining taxes of products and order lines.
#:
#: Determines taxing rules for products, shipping/payment methods and
#: other order lines.  See :obj:`shoop.core.taxing` for details.
SHOOP_TAX_MODULE = "default_tax"

#: TODO: Document SHOOP_ENABLE_ATTRIBUTES
SHOOP_ENABLE_ATTRIBUTES = True

#: TODO: Document SHOOP_ENABLE_MULTIPLE_SHOPS
SHOOP_ENABLE_MULTIPLE_SHOPS = False

#: TODO: Document SHOOP_ADDRESS_HOME_COUNTRY
SHOOP_ADDRESS_HOME_COUNTRY = None


#: TODO: Document SHOOP_ORDER_LINE_TOTAL_DECIMALS
# TODO: (TAX) Is this really needed? Shouldn't order lines be stored with full precision
# and rendered with precision of the used currency conventions?
SHOOP_ORDER_LINE_TOTAL_DECIMALS = 2

#: TODO: Document SHOOP_ORDER_TOTAL_DECIMALS
SHOOP_ORDER_TOTAL_DECIMALS = 2

#: TODO: Document SHOOP_ORDER_LABELS
SHOOP_ORDER_LABELS = [
    (u"default", u"Oletus"),
]

#: TODO: Document SHOOP_DEFAULT_ORDER_LABEL
SHOOP_DEFAULT_ORDER_LABEL = u"default"

#: TODO: Document SHOOP_ORDER_KNOWN_PAYMENT_DATA_KEYS
SHOOP_ORDER_KNOWN_PAYMENT_DATA_KEYS = []

#: TODO: Document SHOOP_ORDER_KNOWN_SHIPPING_DATA_KEYS
SHOOP_ORDER_KNOWN_SHIPPING_DATA_KEYS = []

#: TODO: Document SHOOP_ORDER_KNOWN_EXTRA_DATA_KEYS
SHOOP_ORDER_KNOWN_EXTRA_DATA_KEYS = []
