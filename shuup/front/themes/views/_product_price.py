# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import decimal

from shuup.core.models import ProductVariationResult, ShopProduct, Supplier
from shuup.front.views.product import ProductDetailView
from shuup.utils.numbers import parse_simple_decimal


class ProductPriceView(ProductDetailView):
    template_name = "shuup/front/product/detail_order_section.jinja"

    def get_object(self, queryset=None):
        product = super(ProductPriceView, self).get_object(queryset)
        vars = self.get_variation_variables()
        if vars:
            return ProductVariationResult.resolve(product, vars)
        else:
            return product

    def is_orderable(self):
        product = self.object
        try:
            shop_product = product.get_shop_instance(self.request.shop, allow_cache=True)
        except ShopProduct.DoesNotExist:
            return False
        quantity = self._get_quantity(shop_product)
        if not quantity:
            return False
        if not shop_product.is_orderable(None, self.request.customer, quantity):
            return False
        return True

    def get_context_data(self, **kwargs):
        context = super(ProductPriceView, self).get_context_data(**kwargs)
        if not context["product"] or not self.is_orderable():
            self.template_name = "shuup/front/product/detail_order_section_no_product.jinja"
            return context

        product = self.object
        try:
            shop_product = product.get_shop_instance(self.request.shop, allow_cache=True)
        except ShopProduct.DoesNotExist:
            return False
        quantity = self._get_quantity(shop_product)
        if quantity is not None:
            context["quantity"] = context["product"].sales_unit.round(quantity)

        supplier_pk = self.request.GET.get("supplier", None)
        if supplier_pk is not None:
            context["supplier"] = Supplier.objects.enabled().filter(pk=int(supplier_pk)).first()
        else:
            context["supplier"] = shop_product.get_supplier(
                customer=self.request.customer,
                quantity=(quantity or shop_product.minimum_purchase_quantity))

        return context

    def _get_quantity(self, shop_product):
        quantity_text = self.request.GET.get("quantity", '')
        quantity = parse_simple_decimal(quantity_text, None)
        if quantity is None or quantity < 0:
            return None
        unit_type = self.request.GET.get('unitType', 'internal')
        if unit_type == 'internal':
            return quantity
        else:
            return shop_product.unit.from_display(decimal.Decimal(quantity))

    def get_variation_variables(self):
        return dict(
            (int(k.split("_")[-1]), int(v))
            for (k, v) in self.request.GET.items()
            if k.startswith("var_")
        )

    def get(self, request, *args, **kwargs):
        # Skipping ProductPriceView.super for a reason.
        return super(ProductDetailView, self).get(request, *args, **kwargs)


def product_price(request):
    return ProductPriceView.as_view()(request, pk=request.GET["id"])
