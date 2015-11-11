# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from shoop.core.models import ShopProduct
from shoop.core.pricing import PriceInfo, PricingModule

from .models import CgpPrice


def _get_customer_group_ids(customer):
    # TODO: add caching of some sort
    if customer.is_anonymous:
        return set()
    return set(customer.groups.all().values_list("id", flat=True))


class CustomerGroupPricingModule(PricingModule):
    identifier = "customer_group_pricing"
    name = _("Customer Group Pricing")

    def get_price_info(self, context, product, quantity=1):
        shop = context.shop

        if isinstance(product, six.integer_types):
            product_id = product
            shop_product = ShopProduct.objects.get(product_id=product_id, shop=shop)
        else:
            shop_product = product.get_shop_instance(shop)
            product_id = product.pk

        default_price = (shop_product.default_price_value or 0)

        customer_group_ids = _get_customer_group_ids(context.customer)

        if customer_group_ids:
            filter = Q(
                price_value__gt=0, product=product_id, shop=shop,
                group__in=customer_group_ids)
            result = (
                CgpPrice.objects.filter(filter)
                .order_by("price_value")[:1]
                .values_list("price_value", flat=True)
            )
        else:
            result = None

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
