# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext as _

from shuup.core.models import ProductVariationResult
from shuup.front.views.product import ProductDetailView


class ProductPriceView(ProductDetailView):
    template_name = "shuup/front/product/_detail_order_section.jinja"

    def get_context_data(self, **kwargs):
        context = super(ProductPriceView, self).get_context_data(**kwargs)
        vars = self.get_variation_variables()
        if vars:  # complex variation variables detected
            context["product"] = ProductVariationResult.resolve(context["product"], vars)
            if not context["product"]:
                self.template_name = "shuup/front/product/_detail_order_section_no_product.jinja"
        context["quantity"] = self.request.GET.get("quantity")

        if context["product"]:  # Might be null from ProductVariationResult resolution
            context["quantity"] = context["product"].sales_unit.round(context["quantity"])

        return context

    def get_variation_variables(self):
        return dict(
            (int(k.split("_")[-1]), int(v))
            for (k, v) in self.request.GET.items()
            if k.startswith("var_")
        )

    def get(self, request, *args, **kwargs):
        # `ProductDetailView` issues redirects for variation children, so we override
        # this here.
        product = self.object = self.get_object()
        shop_product = self.shop_product = product.get_shop_instance(request.shop)

        if not shop_product:
            errors = [_("This product is not available in this shop.")]
        else:
            errors = list(shop_product.get_visibility_errors(customer=request.customer))

        if errors:
            return self.render_to_response({"product": None, "error": "\n".join(errors)})

        # Skipping ProductPriceView.super for a reason.
        return super(ProductDetailView, self).get(request, *args, **kwargs)


def product_price(request):
    return ProductPriceView.as_view()(request, pk=request.GET["id"])
