# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
"""
Discount Pricing Module.

This module handles basic discounts for products.

If the discounted price is higher than the
`~shoop.core.models.ShopProduct.default_price`, the lower will be used.

Example:

  If ``default_price`` is 50 and discounted price is 20, the effective
  product price will be 20.
"""

import six
from django.utils.translation import ugettext_lazy as _

from shoop.core.models import ShopProduct
from shoop.core.pricing import PriceInfo, PricingContext, PricingModule

from .models import DiscountedProductPrice


class DiscountPricingContext(PricingContext):
    REQUIRED_VALUES = ["shop"]
    shop = None


class DiscountPricingModule(PricingModule):
    identifier = "discount_pricing"
    name = _("Discount Pricing")

    pricing_context_class = DiscountPricingContext

    def get_context_from_request(self, request):
        return self.pricing_context_class(
            shop=request.shop,
        )

    def get_price_info(self, context, product, quantity=1):
        shop = context.shop

        if isinstance(product, six.integer_types):
            product_id = product
            shop_product = ShopProduct.objects.get(product_id=product_id, shop=shop)
        else:
            shop_product = product.get_shop_instance(shop)
            product_id = product.pk

        default_price = (shop_product.default_price_value or 0)

        result = (
            DiscountedProductPrice.objects
            .filter(product=product_id, shop=shop)
            .order_by("price_value")[:1]
            .values_list("price_value", flat=True)
        )

        price = (min(result[0], default_price) if result else default_price)

        return PriceInfo(
            price=shop.create_price(price * quantity),
            base_price=shop.create_price(default_price * quantity),
            quantity=quantity,
        )
