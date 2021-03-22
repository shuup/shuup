# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import ShopProduct
from shuup.core.pricing import PriceInfo, PricingModule
from shuup.testing.models import SupplierPrice
from shuup.utils.importing import cached_load


class SupplierPricingModule(PricingModule):
    identifier = "supplier_pricing"
    name = _("Supplier Pricing")

    def get_price_info(self, context, product, quantity=1):
        product_id = product if isinstance(product, six.integer_types) else product.pk
        shop = context.shop

        # By default let's use supplier passed to context.
        supplier = context.supplier
        if not supplier:
            # Since supplier is optional I am pretty sure
            # there is cases that supplier is not passed to
            # pricing context. This is not a problem. The
            # pricing module which decides to use supplier
            # for product prices mjust need to have some sane
            # fallback.
            supplier_strategy = cached_load("SHUUP_SHOP_PRODUCT_SUPPLIERS_STRATEGY")
            kwargs = {
                "product_id": product_id,
                "shop": context.shop,
                "customer": context.customer,
                "quantity": quantity,
                "basket": context.basket,
            }

            # Since this is custom pricing module it
            # requires also custom supplier strategy.
            # Some example is provided in
            # `shuup.testing.supplier_pricing.supplier_strategy:CheapestSupplierPriceSupplierStrategy`
            supplier = supplier_strategy().get_supplier(**kwargs)

        # Like now in customer group pricing let's take default price from shop product
        default_price_values = list(
            ShopProduct.objects.filter(product_id=product_id, shop=shop).values_list("default_price_value", flat=True)
        )
        if len(default_price_values) == 0:  # No shop product
            return PriceInfo(price=shop.create_price(0), base_price=shop.create_price(0), quantity=quantity)
        else:
            default_price = default_price_values[0] or 0

        # Then the actual supplier price in case we have
        # been able to figure out some supplier. I guess
        # it is problem for supplier strategy if it allows
        # supplier to be None in some weird scenarios.
        # Not sure though what would happen in shop product
        # orderability checks and so on.
        price = None
        if supplier:
            result = (
                SupplierPrice.objects.filter(shop=shop, product_id=product_id, supplier=supplier)
                .order_by("amount_value")[:1]
                .values_list("amount_value", flat=True)
            )
            if result:
                price = result[0]

            if not price:
                price = default_price

        return PriceInfo(
            price=shop.create_price(price * quantity),
            base_price=shop.create_price(price * quantity),
            quantity=quantity,
        )
