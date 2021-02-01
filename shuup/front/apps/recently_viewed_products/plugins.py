# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import Product
from shuup.core.utils.static import get_shuup_static_url
from shuup.xtheme import TemplatedPlugin
from shuup.xtheme.resources import add_resource


class RecentlyViewedProductsPlugin(TemplatedPlugin):
    identifier = "recently_viewed_products"
    name = _("Recently Viewed Products List")
    template_name = "shuup/recently_viewed_products/list_view.jinja"

    def get_context_data(self, context):
        context = super(RecentlyViewedProductsPlugin, self).get_context_data(context)
        request = context["request"]
        product_ids = [int(pid) for pid in request.COOKIES.get("rvp", "").split(",") if pid != ""]
        context["products"] = sorted(Product.objects.listed(
            customer=request.customer,
            shop=request.shop
        ).filter(id__in=product_ids), key=lambda p: product_ids.index(p.pk))
        return context


def add_resources(context, content):
    view_class = getattr(context["view"], "__class__", None) if context.get("view") else None
    if not view_class:
        return
    view_name = getattr(view_class, "__name__", "")
    if view_name == "ProductDetailView":
        add_resource(context, "body_end", get_shuup_static_url("shuup/recently_viewed_products/lib.js"))
