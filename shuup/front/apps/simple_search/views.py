# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import hashlib
import re

from django import forms
from django.db.models import Q
from django.utils.encoding import force_bytes
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView

from shuup.core import cache
from shuup.core.models import Product
from shuup.front.template_helpers.product import is_visible
from shuup.front.utils.product_sorting import (
    PRODUCT_SORT_CHOICES, sort_products
)
from shuup.front.utils.views import cache_product_things


def get_query_words(query):
    """
    Get query words

    Split the query into words and return a list of strings.

    :type query_string: str
    :return: List of strings
    :rtype: list
    """
    word_finder = re.compile(r'"([^"]+)"|(\S+)').findall
    normalize_spaces = re.compile(r'\s{2,}').sub
    words = []
    for word in word_finder(query):
        found_word = word[0] or word[1]
        words.append(normalize_spaces(" ", found_word.strip()))
    return words


def get_compiled_query(query_string, needles):
    """
    Get compiled query

    Complile query string into `Q` objects and return it
    """
    compiled_query = None
    for word in get_query_words(query_string):
        inner_query = None
        for needle in needles:
            q = Q(**{"%s__icontains" % needle: word})
            inner_query = q if inner_query is None else inner_query | q
        compiled_query = inner_query if compiled_query is None else compiled_query & inner_query
    return compiled_query


def get_search_product_ids(request, query):
    query = query.strip().lower()
    cache_key = "simple_search:%s" % hashlib.sha1(force_bytes(query)).hexdigest()
    product_ids = cache.get(cache_key)
    if product_ids is None:
        entry_query = get_compiled_query(
            query, ['translations__name', 'translations__description', 'translations__keywords'])
        product_ids = Product.objects.filter(entry_query).distinct().values_list("pk", flat=True)
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
    template_name = "shuup/simple_search/search.jinja"
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
