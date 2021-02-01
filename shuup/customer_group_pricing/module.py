# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import ShopProduct
from shuup.core.pricing import DiscountModule, PriceInfo, PricingModule

from .models import CgpDiscount, CgpPrice


class CustomerGroupPricingModule(PricingModule):
    identifier = "customer_group_pricing"
    name = _("Customer Group Pricing")

    def get_price_info(self, context, product, quantity=1):
        shop = context.shop
        product_id = (product if isinstance(product, six.integer_types) else product.pk)
        default_price_values = list(ShopProduct.objects.filter(
            product_id=product_id, shop=shop).values_list("default_price_value", flat=True))

        if len(default_price_values) == 0:  # No shop product
            return PriceInfo(price=shop.create_price(0), base_price=shop.create_price(0), quantity=quantity)
        else:
            default_price = default_price_values[0] or 0

        filter = Q(
            product_id=product_id, shop=shop,
            price_value__gt=0,
            group__in=context.customer.groups.all())
        result = (
            CgpPrice.objects.filter(filter)
            .order_by("price_value")[:1]
            .values_list("price_value", flat=True)
        )

        if result:
            price = result[0]
            if default_price > 0:
                price = min([default_price, price])
        else:
            price = default_price

        return PriceInfo(
            price=shop.create_price(price * quantity),
            base_price=shop.create_price(price * quantity),
            quantity=quantity,
        )


class CustomerGroupDiscountModule(DiscountModule):
    identifier = "customer_group_discount"
    name = _("Customer Group Discount")

    def discount_price(self, context, product, price_info):
        """
        Get the best discount amount for context.
        """
        shop = context.shop
        product_id = product if isinstance(product, six.integer_types) else product.pk

        cgp_discount = CgpDiscount.objects.filter(
            shop_id=shop.id,
            product_id=product_id,
            group__in=context.customer.groups.all(),
            discount_amount_value__gt=0,
        ).order_by("-discount_amount_value").first()

        if cgp_discount:
            total_discount = cgp_discount.discount_amount * price_info.quantity
            # do not allow the discount to be greater than the price
            price_info.price = max(price_info.price - total_discount, context.shop.create_price(0))

        return price_info
