# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _

from shoop.core.models import ShopProduct
from shoop.core.pricing import PriceInfo, PricingContext, PricingModule


class DefaultPricingContext(PricingContext):
    REQUIRED_VALUES = ["shop"]
    shop = None


class DefaultPricingModule(PricingModule):
    identifier = "default_pricing"
    name = _("Default Pricing")

    pricing_context_class = DefaultPricingContext

    def get_context_from_request(self, request):
        """
        Inject shop into pricing context.

        Shop information is used to find correct `ShopProduct`
        in `self.get_price_info`
        """
        return self.pricing_context_class(shop=request.shop)

    def get_price_info(self, context, product, quantity=1):
        """
        Return a `PriceInfo` calculated from `ShopProduct.default_price`

        Since `ShopProduct.default_price` can be `None` it will
        be set to zero (0) if `None`.
        """
        shop = context.shop
        shop_product = ShopProduct.objects.get(product=product, shop=shop)

        default_price = (shop_product.default_price_value or 0)

        return PriceInfo(
            price=shop.create_price(default_price * quantity),
            base_price=shop.create_price(default_price * quantity),
            quantity=quantity,
        )
