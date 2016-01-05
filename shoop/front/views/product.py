# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.utils.translation import get_language
from django.views.generic import DetailView

from shoop.core.models import Product, ProductMode
from shoop.front.utils.views import cache_product_things
from shoop.utils.excs import extract_messages, Problem
from shoop.utils.numbers import get_string_sort_order


class ProductDetailView(DetailView):
    template_name = "shoop/front/product/detail.jinja"
    model = Product
    context_object_name = "product"

    def get_queryset(self):
        return Product.objects.language(get_language()).select_related("primary_image")

    def get_context_data(self, **kwargs):
        context = super(ProductDetailView, self).get_context_data(**kwargs)
        language = self.language = get_language()
        product = self.object
        context["category"] = self.shop_product.primary_category
        context["orderability_errors"] = list(self.shop_product.get_orderability_errors(
            supplier=None,
            quantity=1,
            customer=self.request.customer,
            ignore_minimum=True
        ))
        context["variation_children"] = []
        if product.mode == ProductMode.SIMPLE_VARIATION_PARENT:
            context["variation_children"] = cache_product_things(
                self.request,
                sorted(
                    product.variation_children.language(language).all(),
                    key=lambda p: get_string_sort_order(p.variation_name or p.name)
                )
            )
            context["orderable_variation_children"] = [
                p for p in context["variation_children"]
                if p.get_shop_instance(self.request.shop).is_orderable(
                    supplier=None,
                    customer=self.request.customer,
                    quantity=1
                )
            ]
        elif product.mode == ProductMode.VARIABLE_VARIATION_PARENT:
            context["variation_variables"] = product.variation_variables.all().prefetch_related("values")
        elif product.mode == ProductMode.PACKAGE_PARENT:
            children = (
                product.package_children
                .language(language)
                .order_by("translations__name")
                .all())
            context["package_children"] = cache_product_things(self.request, children)

        context["shop_product"] = self.shop_product

        primary_image = None
        if self.shop_product.shop_primary_image_id:
            primary_image = self.shop_product.shop_primary_image
        elif product.primary_image_id:
            primary_image = self.shop_product.primary_image

        context["primary_image"] = primary_image
        context["images"] = self.shop_product.images.all()

        # TODO: Maybe add hook for ProductDetailView get_context_data?
        # dispatch_hook("get_context_data", view=self, context=context)

        return context

    def get(self, request, *args, **kwargs):
        product = self.object = self.get_object()

        if product.mode == ProductMode.VARIATION_CHILD:
            return redirect("shoop:product", pk=product.variation_parent.pk, slug=product.variation_parent.slug)

        shop_product = self.shop_product = product.get_shop_instance(request.shop)
        if not shop_product:
            raise Problem(_(u"This product is not available in this shop."))

        errors = list(shop_product.get_visibility_errors(customer=request.customer))

        if errors:
            raise Problem("\n".join(extract_messages(errors)))

        return super(ProductDetailView, self).get(request, *args, **kwargs)
