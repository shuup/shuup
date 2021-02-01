# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.front.views.product import ProductDetailView


class ProductPreviewView(ProductDetailView):
    template_name = "shuup/front/product/product_preview.jinja"

    def get_context_data(self, **kwargs):
        # By default the template rendering the basket add form
        # uses the `request.path` as its' `next` value.
        # This is fine if you are on product page but here in
        # preview, we cannot redirect back to `/xtheme/product_preview`.

        context = super(ProductPreviewView, self).get_context_data(**kwargs)
        # Add `return_url` to context to avoid usage of `request.path`
        context["return_url"] = "/xtheme/products"
        return context


def product_preview(request):
    return ProductPreviewView.as_view()(request, pk=request.GET["id"])
