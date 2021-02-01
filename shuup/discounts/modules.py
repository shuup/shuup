# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import ShopProduct
from shuup.core.order_creator import OrderSourceModifierModule
from shuup.core.pricing import DiscountModule
from shuup.discounts.models import CouponCode, CouponUsage
from shuup.discounts.utils import (
    get_active_discount_for_code, get_potential_discounts_for_product,
    get_price_expiration
)


class ProductDiscountModule(DiscountModule):
    identifier = "product_discounts"
    name = _("Product Discounts")

    def discount_price(self, context, product, price_info):
        shop = context.shop
        basket = getattr(context, "basket", None)
        potential_discounts = get_potential_discounts_for_product(context, product).values_list(
            "discounted_price_value", "discount_amount_value", "discount_percentage", "coupon_code__code"
        )

        discounted_prices = []
        for discounted_price_value, discount_amount_value, discount_percentage, coupon_code in potential_discounts:
            if basket and coupon_code and not CouponCode.is_usable(shop, coupon_code, customer=basket.customer):
                # TODO: Revise! This will cause some queries. Are do we want those? Maybe some cache for this check?
                # Maybe somewhere we should just remove coupon codes that is not usable from basket all together?
                continue

            if discounted_price_value:  # Applies the new product price per item
                discounted_prices.append(
                    min(
                        price_info.price,
                        max(
                            shop.create_price(discounted_price_value) * price_info.quantity,
                            shop.create_price(0)
                        )
                    )
                )

            if discount_amount_value:  # Discount amount value per item
                discounted_prices.append(
                    max(
                        price_info.price - shop.create_price(discount_amount_value) * price_info.quantity,
                        shop.create_price(0)
                    )
                )

            if discount_percentage:  # Discount percentage per item
                discounted_prices.append(
                    max(
                        price_info.price - price_info.price * discount_percentage,
                        shop.create_price(0)
                    )
                )

        if discounted_prices:
            product_id = (product if isinstance(product, six.integer_types) else product.pk)
            minimum_price_values = list(ShopProduct.objects.filter(
                product_id=product_id, shop=shop).values_list("minimum_price_value", flat=True))

            minimum_price_value = minimum_price_values[0] if minimum_price_values else 0

            price_info.price = max(
                min(discounted_prices),
                shop.create_price(minimum_price_value or 0) or shop.create_price(0)
            )

        price_expiration = get_price_expiration(context, product)
        if price_expiration and (not price_info.expires_on or price_expiration < price_info.expires_on):
            price_info.expires_on = price_expiration

        return price_info


class CouponCodeModule(OrderSourceModifierModule):
    identifier = "discounts_coupon_codes"
    name = _("Product Discounts Coupon Codes")

    def can_use_code(self, order_source, code):
        active_discount = get_active_discount_for_code(order_source, code)
        if not active_discount:
            return False

        return active_discount.coupon_code.can_use_code(order_source.shop, order_source.customer)

    def use_code(self, order, code):
        active_discount = get_active_discount_for_code(order, code)
        if not active_discount:  # TODO: Revise! Likely "shouldn't" happen too often
            return

        return active_discount.coupon_code.use(order)

    def clear_codes(self, order):
        CouponUsage.objects.filter(order=order).delete()
