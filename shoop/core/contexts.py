# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.core.pricing import PricingContext, get_pricing_module
from shoop.core.taxing import TaxingContext, get_tax_module


class PriceTaxContext(object):
    def __init__(self, pricing_context, taxing_context):
        """
        Initialize context for pricing and taxing.
        """
        assert isinstance(pricing_context, PricingContext)
        assert isinstance(taxing_context, TaxingContext)
        self.pricing_context = pricing_context
        self.taxing_context = taxing_context

    @classmethod
    def from_request(cls, request):
        return cls(
            pricing_context=get_pricing_module().get_context(request),
            taxing_context=get_tax_module().get_context(request)
        )
