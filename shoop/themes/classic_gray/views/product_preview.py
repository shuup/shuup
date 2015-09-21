# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.front.views.product import ProductDetailView


def product_preview(request):
    return ProductDetailView.as_view(template_name="classic_gray/product_preview.jinja")(
        request, pk=request.GET["id"]
    )
