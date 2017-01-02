# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.core.models import ProductVariationResult
from shuup.front.views.product import ProductDetailView


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
        if not product:
            return False
        shop_product = product.get_shop_instance(self.request.shop)
        qty = int(self.request.GET.get("quantity", 1))
        if not shop_product.is_orderable(None, self.request.customer, qty):
            return False
        return True

    def get_context_data(self, **kwargs):
        context = super(ProductPriceView, self).get_context_data(**kwargs)
        if not context["product"] or not self.is_orderable():
            self.template_name = "shuup/front/product/detail_order_section_no_product.jinja"
            return context
        context["quantity"] = context["product"].sales_unit.round(self.request.GET.get("quantity"))
        return context

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
