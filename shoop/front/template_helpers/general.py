# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.paginator import Paginator
from django.utils.translation import get_language
from jinja2.utils import contextfunction
from mptt.templatetags.mptt_tags import cache_tree_children

from shoop.core.models import Category, Manufacturer, Product
from shoop.front.utils.product_statistics import get_best_selling_product_info
from shoop.front.utils.views import cache_product_things
from shoop.utils.translation import cache_translations_for_tree


def _get_list_products(request):
    return Product.objects.list_visible(
        shop=request.shop,
        customer=request.customer,
        language=get_language(),
    )


# @contextfunction
# def get_recommended_products(context):
#     func = cached_load("SHOP_GLOBAL_RECOMMENDED_PRODUCTS_SPEC", lambda request: [])
#     request = context["request"]
#     products = func(request)
#     if products and any(not p for p in products):
#         fillins = list(get_best_selling_products(context)) + list(get_newest_products(context))
#         if settings.SHOP_ENABLE_VARIATIONS:
#             fillins = list(set((p.variation_parent or p) for p in fillins))
#         random.shuffle(fillins)
#         products = [(p if p else (fillins.pop(0) if fillins else None)) for p in products]
#     products = [p for p in products if p and p.is_visible()]
#     cache_product_things(request, products)
#     return products


@contextfunction
def get_best_selling_products(context, n_products=12, cutoff_days=30, no_variation_children=False):
    request = context["request"]
    data = get_best_selling_product_info(
        shop_ids=[request.shop.pk],
        cutoff_days=cutoff_days
    )
    product_ids = [d[0] for d in data][:n_products * 2]
    products = _get_list_products(request).filter(id__in=product_ids)
    if no_variation_children:  # pragma: no branch
        products = products.filter(variation_parent=None)
    products = cache_product_things(request, products)
    products = sorted(products, key=lambda p: product_ids.index(p.id))  # pragma: no branch
    products = products[:n_products]
    return products


@contextfunction
def get_newest_products(context, n_products=6):
    request = context["request"]
    products = _get_list_products(request).order_by("-pk")[:n_products]
    products = cache_product_things(request, products)
    return products


@contextfunction
def get_random_products(context, n_products=6):
    request = context["request"]
    products = _get_list_products(request).order_by("?")[:n_products]
    products = cache_product_things(request, products)
    return products


@contextfunction
def get_all_manufacturers(context):
    request = context["request"]
    products = Product.objects.list_visible(shop=request.shop, customer=request.customer)
    manufacturers_ids = products.values_list("manufacturer__id").distinct()
    manufacturers = Manufacturer.objects.filter(pk__in=manufacturers_ids)
    return manufacturers


@contextfunction
def get_root_categories(context):
    request = context["request"]
    language = get_language()
    roots = cache_tree_children(
        Category.objects.all_visible(
            customer=request.customer, shop=request.shop, language=language))
    cache_translations_for_tree(roots, languages=[language])
    return roots


@contextfunction
def get_pagination_variables(context, objects, limit):
    """
    Get pagination variables for template

    :param context: template context
    :param objects: objects paginated
    :param limit: per page limit
    :return: variables to render object-list with pagination
    """
    variables = {"objects": objects}

    variables["paginator"] = paginator = Paginator(objects, limit)
    variables["is_paginated"] = (paginator.num_pages > 1)
    try:
        current_page = int(context["request"].GET.get("page") or 0)
    except ValueError:
        current_page = 1
    page = paginator.page(min((current_page or 1), paginator.num_pages))
    variables["page"] = page
    variables["objects"] = page.object_list

    return variables
