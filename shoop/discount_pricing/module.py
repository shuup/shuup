# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

"""
Discount Pricing Module

This module handles basic discounts for `ShopProduct`s

If the discounted price is higher than `ShopProduct.default_price`
the latter will be used as price.

Example:
If `ShopProduct.default_price` is set to 50 and discounted
price of 20 is added the product will be sold for 20 from
that point forward.
"""


import six
from django.utils.translation import ugettext_lazy as _

from shoop.core.models import ShopProduct
from shoop.core.pricing import PriceInfo, PricingContext, PricingModule, TaxfulPrice, TaxlessPrice

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

        if isinstance(product, six.integer_types):
            product_id = product
            shop_product = ShopProduct.objects.get(product_id=product_id, shop_id=context.shop.pk)
        else:
            shop_product = product.get_shop_instance(context.shop)
            product_id = product.pk

        default_price = (shop_product.default_price or 0)

        includes_tax = context.shop.prices_include_tax

        result = (DiscountedProductPrice.objects.filter(product=product_id, shop=context.shop)
                  .order_by("price")[:1]
                  .values_list("price", flat=True)
                  )

        if result:
            price = result[0]
            if price > default_price:
                price = default_price
        else:
            price = default_price

        price_cls = (TaxfulPrice if includes_tax else TaxlessPrice)
        return PriceInfo(
            price=price_cls(price * quantity),
            base_price=price_cls(default_price * quantity),
            quantity=quantity,
        )
