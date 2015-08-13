# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from shoop.core.pricing import PricingContext, PricingModule, TaxfulPrice, TaxlessPrice

from .models import SimpleProductPrice


class SimplePricingContext(PricingContext):
    REQUIRED_VALUES = ("customer_group_ids", "shop_id")
    customer_group_ids = ()
    shop_id = None


class SimplePricingModule(PricingModule):
    identifier = "simple_pricing"
    name = _("Simple Pricing")

    pricing_context_class = SimplePricingContext

    def get_context_from_request(self, request):
        customer = getattr(request, "customer", None)
        shop = getattr(request, "shop", None)

        if not customer or customer.is_anonymous:
            customer_group_ids = []
        else:
            customer_group_ids = sorted(customer.groups.all().values_list("id", flat=True))

        return self.pricing_context_class(
            shop_id=(shop.pk if shop else None),
            customer_group_ids=customer_group_ids
        )

    def get_price(self, context, product_id, quantity=1):
        # TODO: SimplePricingModule: Implement caching that works

        filter = Q(price__gt=0, product_id=product_id)

        if context.customer_group_ids:
            filter &= (Q(group__id__in=context.customer_group_ids) | Q(group__isnull=True))
        else:
            filter &= Q(group__isnull=True)

        if context.shop_id:
            filter &= (Q(shop_id=context.shop_id) | Q(shop__isnull=True))
        else:
            filter &= Q(shop__isnull=True)

        result = (
            SimpleProductPrice.objects.filter(filter)
            .order_by("price")[:1]
            .values_list("price", "includes_tax")
        )

        (price, includes_tax) = result[0] if result else (0, False)
        return _create_price(price, includes_tax)

    def get_base_price(self, product):
        product_price_model = SimpleProductPrice.objects.filter(product=product, group=None).first()
        if product_price_model:
            return _create_price(product_price_model.price, product_price_model.includes_tax)

        return _create_price(0, includes_tax=False)


def _create_price(price, includes_tax):
    if includes_tax:
        return TaxfulPrice(price)
    else:
        return TaxlessPrice(price)
