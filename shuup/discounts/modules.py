# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.utils.translation import ugettext_lazy as _
from typing import Union

from shuup.core.models import AnonymousContact, ProductCatalogDiscountedPrice, ShopProduct
from shuup.core.pricing import DiscountModule, PriceInfo
from shuup.discounts.utils import get_potential_discounts_for_product, get_price_expiration, index_shop_product_price


class ProductDiscountModule(DiscountModule):
    identifier = "product_discounts"
    name = _("Product Discounts")

    def discount_price(self, context, product, price_info):
        shop = context.shop
        potential_discounts = get_potential_discounts_for_product(context, product).values_list(
            "discounted_price_value",
            "discount_amount_value",
            "discount_percentage",
        )

        discounted_prices = []
        for discounted_price_value, discount_amount_value, discount_percentage in potential_discounts:
            if discounted_price_value:  # Applies the new product price per item
                discounted_prices.append(
                    min(
                        price_info.price,
                        max(shop.create_price(discounted_price_value) * price_info.quantity, shop.create_price(0)),
                    )
                )

            if discount_amount_value:  # Discount amount value per item
                discounted_prices.append(
                    max(
                        price_info.price - shop.create_price(discount_amount_value) * price_info.quantity,
                        shop.create_price(0),
                    )
                )

            if discount_percentage:  # Discount percentage per item
                discounted_prices.append(
                    max(price_info.price - price_info.price * discount_percentage, shop.create_price(0))
                )

        new_price_info = PriceInfo(
            price=price_info.price,
            base_price=price_info.base_price,
            quantity=price_info.quantity,
            expires_on=price_info.expires_on,
        )

        if discounted_prices:
            product_id = product if isinstance(product, six.integer_types) else product.pk
            minimum_price_values = list(
                ShopProduct.objects.filter(product_id=product_id, shop=shop).values_list(
                    "minimum_price_value", flat=True
                )
            )

            minimum_price_value = minimum_price_values[0] if minimum_price_values else 0
            new_price_info.price = max(
                min(discounted_prices), shop.create_price(minimum_price_value or 0) or shop.create_price(0)
            )

        price_expiration = get_price_expiration(context, product)
        if price_expiration and (not price_info.expires_on or price_expiration < price_info.expires_on):
            new_price_info.expires_on = price_expiration

        return new_price_info

    def index_shop_product(self, shop_product: Union["ShopProduct", int], **kwargs):
        """
        Index the shop product discounts. This is a heavy procedure, use with precaution
        and through some background task.
        """
        if isinstance(shop_product, int):
            shop_product = ShopProduct.objects.select_related("product", "shop").get(pk=shop_product)

        is_variation_parent = shop_product.product.is_variation_parent()

        # index the discounted price of all children shop products
        if is_variation_parent:
            children_shop_product = ShopProduct.objects.select_related("product", "shop").filter(
                shop=shop_product.shop, product__variation_parent=shop_product.product
            )
            for child_shop_product in children_shop_product:
                self.index_shop_product(child_shop_product)
        else:
            ProductCatalogDiscountedPrice.objects.filter(
                catalog_rule__module_identifier=self.identifier, shop=shop_product.shop, product=shop_product.product
            ).delete()

            from shuup.discounts.models import Discount

            # get the different contact groups ids to index the prices
            discounts_groups_ids = list(
                Discount.objects.filter(
                    shop=shop_product.shop,
                    active=True,
                    contact_group__isnull=False,
                )
                .values_list("contact_group__id", flat=True)
                .distinct()
            )
            discounts_groups_ids.append(AnonymousContact.get_default_group().pk)

            for supplier in shop_product.suppliers.all().only("pk"):
                index_shop_product_price(shop_product, supplier, discounts_groups_ids)
