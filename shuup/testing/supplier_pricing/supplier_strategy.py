# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.core.models import Supplier
from shuup.testing.models import SupplierPrice


class CheapestSupplierPriceSupplierStrategy(object):

    def get_supplier(self, **kwargs):
        # Here we did some trick and passed different
        # kwargs than is passed from shop product get
        # supplier. Shouldn't be issue as long as this
        # strategy is able to adjust to both set of
        # kwargs.
        product_id = kwargs.get("product_id")
        if not product_id:
            shop_product = kwargs.get("shop_product")
            if not shop_product:
                return
            product_id = shop_product.product.pk

        shop = kwargs.get("shop")
        if not shop:
            shop_product = kwargs.get("shop_product")
            if not shop_product:
                return
            shop = shop_product.shop

        # Supplier with best price and fallback to
        # first shop product supplier. Likely there
        # needs to be cache around this in real solution,
        # but this is just a testing strategy to help
        # test supplier prices and multiple suppliers
        # with front.
        enabled_suppliers = Supplier.objects.enabled(shop=shop)

        supplier_price = SupplierPrice.objects.filter(
            shop=shop,
            product_id=product_id,
            supplier__in=enabled_suppliers
        ).select_related("supplier").order_by("amount_value").first()

        if supplier_price:
            return supplier_price.supplier

        return enabled_suppliers.filter(shop_products__product__id=product_id).first()
