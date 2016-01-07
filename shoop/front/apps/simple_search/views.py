# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import hashlib

from django import forms
from django.db.models import Q
from django.utils.encoding import force_bytes
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView

from shoop.core import cache
from shoop.core.models import Product
from shoop.front.template_helpers.product import is_visible
from shoop.front.utils.product_sorting import (
    PRODUCT_SORT_CHOICES, sort_products
)
from shoop.front.utils.views import cache_product_things


def get_search_product_ids(request, query):
    query = query.strip().lower()
    cache_key = "simple_search:%s" % hashlib.sha1(force_bytes(query)).hexdigest()
    product_ids = cache.get(cache_key)
    if product_ids is None:
        product_ids = Product.objects.filter(
            Q(translations__name__icontains=query) |
            Q(translations__description__icontains=query) |
            Q(translations__keywords__icontains=query)
        ).distinct().values_list("pk", flat=True)
        cache.set(cache_key, product_ids, 60 * 5)
    return product_ids


class SearchForm(forms.Form):
    q = forms.CharField(label=_("Search"))
    sort = forms.CharField(
        required=False,
        widget=forms.Select(choices=PRODUCT_SORT_CHOICES),
        label=_("Sort")
    )

    def clean(self):
        self.cleaned_data["q"] = self.cleaned_data["q"].strip()


class SearchView(ListView):
    form_class = SearchForm
    template_name = "shoop/simple_search/search.jinja"
    model = Product
    context_object_name = "products"

    def dispatch(self, request, *args, **kwargs):
        q = self.request.REQUEST.get("q")
        if q:
            data = dict(self.request.REQUEST)
        else:
            data = None
        self.form = SearchForm(data=data)
        return super(SearchView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if not self.form.is_valid():
            return Product.objects.none()
        query = self.form.cleaned_data["q"]
        if not query:  # pragma: no cover
            return Product.objects.none()
        return Product.objects.list_visible(self.request.shop, self.request.customer).filter(
            pk__in=get_search_product_ids(self.request, query))

    def get_context_data(self, **kwargs):
        context = super(SearchView, self).get_context_data(**kwargs)
        context["form"] = self.form
        products = context["products"]
        if products:
            products = cache_product_things(self.request, products)
            products = sort_products(self.request, products, self.form.cleaned_data.get("sort"))
            products = [p for p in products if is_visible({"request": self.request}, p)]
            context["products"] = products
        context["no_results"] = (self.form.is_valid() and not products)
        return context
