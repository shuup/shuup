# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
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

        try:
            if isinstance(product, six.integer_types):
                product_id = product
                shop_product = ShopProduct.objects.get(product_id=product_id, shop=shop)
            else:
                shop_product = product.get_shop_instance(shop)
                product_id = product.pk
        except ShopProduct.DoesNotExist:
            # shop product does not exist, zero price
            return PriceInfo(price=shop.create_price(0), base_price=shop.create_price(0), quantity=quantity)

        default_price = (shop_product.default_price_value or 0)

        filter = Q(
            product=product_id, shop=shop,
            price_value__gt=0,
            group__in=context.customer.get_contact_groups(shop))
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
            group__in=context.customer.get_contact_groups(shop),
            discount_amount_value__gt=0,
        ).order_by("-discount_amount_value").first()

        if cgp_discount:
            total_discount = cgp_discount.discount_amount * price_info.quantity
            # do not allow the discount to be greater than the price
            price_info.price = max(price_info.price - total_discount, context.shop.create_price(0))

        return price_info
