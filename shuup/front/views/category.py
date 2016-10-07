# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import with_statement

from django.views.generic import DetailView

from shuup.core.models import Category, Product
from shuup.front.utils.sorts_and_filters import (
    get_query_filters, post_filter_products, ProductListForm, sort_products
)
from shuup.front.utils.views import cache_product_things


class CategoryView(DetailView):
    template_name = "shuup/front/product/category.jinja"
    model = Category
    template_object_name = "category"

    def get_queryset(self):
        return self.model.objects.all_visible(
            customer=self.request.customer,
            shop=self.request.shop,
        )

    def get_context_data(self, **kwargs):
        context = super(CategoryView, self).get_context_data(**kwargs)
        category = self.object
        data = self.request.GET
        context["form"] = form = ProductListForm(
            request=self.request, shop=self.request.shop, category=category, data=data)
        form.full_clean()
        data = form.cleaned_data
        if "sort" in form.fields and not data.get("sort"):
            # Use first choice by default
            data["sort"] = form.fields["sort"].widget.choices[0][0]

        products = Product.objects.listed(
            customer=self.request.customer,
            shop=self.request.shop
        ).filter(
            shop_products__shop=self.request.shop,
            variation_parent__isnull=True,
            shop_products__categories=category
        ).filter(get_query_filters(self.request, category, data=data)).distinct()

        products = post_filter_products(self.request, category, products, data)
        products = cache_product_things(self.request, products)
        products = sort_products(self.request, category, products, data)
        context["form_fields"] = [key for key in form.fields.keys()]
        context["products"] = products
        return context
