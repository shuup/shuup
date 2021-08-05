# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.models import Q
from django.views.generic import ListView

from shuup.core.catalog import ProductCatalog, ProductCatalogContext
from shuup.core.models import Product, ProductMode, ShopProductVisibility
from shuup.front.utils.sorts_and_filters import ProductListForm, get_product_queryset, get_query_filters, sort_products


class SearchView(ListView):
    form_class = ProductListForm
    template_name = "shuup/simple_search/search.jinja"
    model = Product
    context_object_name = "products"

    def dispatch(self, request, *args, **kwargs):
        self.form = ProductListForm(request=self.request, shop=self.request.shop, category=None, data=self.request.GET)
        return super(SearchView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if not self.form.is_valid():
            return Product.objects.none()
        data = self.form.cleaned_data
        if not (data and data.get("q")):  # pragma: no cover
            return Product.objects.none()

        catalog = ProductCatalog(
            ProductCatalogContext(
                shop=self.request.shop,
                user=self.request.user,
                contact=getattr(self.request, "customer", None),
                purchasable_only=True,
                visibility=ShopProductVisibility.SEARCHABLE,
            )
        )
        products = catalog.get_products_queryset().filter(
            Q(mode__in=ProductMode.get_parent_modes()), Q(get_query_filters(self.request, None, data=data))
        )
        products = get_product_queryset(products, self.request, None, data)
        products = sort_products(self.request, None, products, data)
        return products.distinct()

    def get_context_data(self, **kwargs):
        context = super(SearchView, self).get_context_data(**kwargs)
        context["form"] = self.form
        products = context["products"]
        context["no_results"] = self.form.is_valid() and not products.exists()
        return context
