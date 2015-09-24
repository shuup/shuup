# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.front.views.product import ProductDetailView


class ProductPriceView(ProductDetailView):
    template_name = "shoop/front/product/_detail_order_section.jinja"

    def get_context_data(self, **kwargs):
        context = super(ProductPriceView, self).get_context_data(**kwargs)
        product = context["product"]
        context["quantity"] = product.sales_unit.round(self.request.GET.get("quantity"))
        context["selected_child"] = int(self.request.GET.get("child") or 0)
        return context


def product_price(request):
    return ProductPriceView.as_view()(request, pk=request.GET["id"])
