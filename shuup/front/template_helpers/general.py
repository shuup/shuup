# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from collections import defaultdict

import six
from django.conf import settings
from django.core.paginator import Paginator
from django.utils.translation import get_language
from jinja2.utils import contextfunction

from shuup.core.models import (
    Category, Manufacturer, Product, ShopProduct, Supplier
)
from shuup.core.utils import context_cache
from shuup.front.utils import cache as cache_utils
from shuup.front.utils.companies import allow_company_registration
from shuup.front.utils.product_statistics import get_best_selling_product_info
from shuup.front.utils.translation import get_language_choices
from shuup.front.utils.user import is_admin_user
from shuup.front.utils.views import cache_product_things
from shuup.utils.importing import cached_load
from shuup.utils.mptt import get_cached_trees
from shuup.utils.translation import cache_translations_for_tree


def get_login_form(request):
    # Getting the form from the Login view
    form = cached_load("SHUUP_LOGIN_VIEW")(request=request).get_form()
    return form


def _group_list_items(group_list, number):
    for i in range(0, len(group_list), number):
        yield tuple(group_list[i: i + number])


def _get_listed_products(context, n_products, ordering=None,    # noqa (C901)
                         filter_dict=None, orderable_only=True,
                         extra_filters=None):
    """
    Returns all products marked as listed that are determined to be
    visible based on the current context.

    :param context: Rendering context
    :type context: jinja2.runtime.Context
    :param n_products: Number of products to return
    :type n_products: int
    :param ordering: String specifying ordering
    :type ordering: str
    :param filter_dict: Dictionary of filter parameters
    :type filter_dict: dict[str, object]
    :param orderable_only: Boolean limiting results to orderable products
    :type orderable_only: bool
    :param extra_filters: Extra filters to be used in Product Queryset
    :type extra_filters: django.db.models.Q
    :rtype: list[shuup.core.models.Product]
    """
    request = context["request"]
    customer = request.customer
    shop = request.shop

    # Todo: Check if this should be cached

    if not filter_dict:
        filter_dict = {}
    products_qs = Product.objects.listed(
        shop=shop,
        customer=customer,
        language=get_language(),
    ).filter(**filter_dict)

    if extra_filters:
        products_qs = products_qs.filter(extra_filters)

    if ordering:
        products_qs = products_qs.order_by(ordering)

    products = list(products_qs.distinct()[:n_products])

    if orderable_only:
        suppliers = Supplier.objects.enabled().filter(shops=shop)
        valid_products = []

        for product in products:
            if len(valid_products) == n_products:
                break
            try:
                shop_product = product.get_shop_instance(shop, allow_cache=True)
            except ShopProduct.DoesNotExist:
                continue

            for supplier in suppliers:
                if shop_product.is_orderable(supplier, customer, shop_product.minimum_purchase_quantity):
                    valid_products.append(product)
                    break

        return valid_products

    return products


@contextfunction
def get_listed_products(context, n_products, ordering=None, filter_dict=None, orderable_only=True, extra_filters=None):
    """
    A cached version of _get_listed_products
    """
    request = context["request"]

    key, products = context_cache.get_cached_value(
        identifier="listed_products",
        item=cache_utils.get_listed_products_cache_item(request.shop),
        context=request,
        n_products=n_products,
        ordering=ordering,
        filter_dict=filter_dict,
        orderable_only=orderable_only,
        extra_filters=hash(str(extra_filters))
    )
    if products is not None:
        return products

    products = _get_listed_products(
        context,
        n_products,
        ordering=ordering,
        filter_dict=filter_dict,
        orderable_only=orderable_only,
        extra_filters=extra_filters
    )
    products = cache_product_things(request, products)
    context_cache.set_cached_value(key, products, settings.SHUUP_TEMPLATE_HELPERS_CACHE_DURATION)
    return products


@contextfunction
def get_best_selling_products(context, n_products=12, cutoff_days=30, orderable_only=True):
    request = context["request"]

    key, products = context_cache.get_cached_value(
        identifier="best_selling_products",
        item=cache_utils.get_best_selling_products_cache_item(request.shop),
        context=request,
        n_products=n_products, cutoff_days=cutoff_days,
        orderable_only=orderable_only
    )

    if products is not None:
        return products

    products = _get_best_selling_products(cutoff_days, n_products, orderable_only, request)
    context_cache.set_cached_value(key, products, settings.SHUUP_TEMPLATE_HELPERS_CACHE_DURATION)
    return products


def _get_best_selling_products(cutoff_days, n_products, orderable_only, request):  # noqa (C901)
    data = get_best_selling_product_info(
        shop_ids=[request.shop.pk],
        cutoff_days=cutoff_days
    )
    combined_variation_products = defaultdict(int)
    for product_id, parent_id, qty in data:
        if parent_id:
            combined_variation_products[parent_id] += qty
        else:
            combined_variation_products[product_id] += qty

    # get all the product ids
    product_ids = [
        d[0] for
        d in sorted(six.iteritems(combined_variation_products), key=lambda i: i[1], reverse=True)
    ]

    # group product ids in groups of n_products
    # to prevent querying ALL products at once
    products = []
    for grouped_product_ids in _group_list_items(product_ids, n_products):
        valid_products_qs = Product.objects.listed(
            shop=request.shop,
            customer=request.customer
        ).filter(
            id__in=grouped_product_ids,
            shop_products__shop=request.shop,
            shop_products__suppliers__enabled=True
        )
        for product in valid_products_qs.iterator():
            products.append(product)

            if len(products) == n_products:
                break

        if len(products) == n_products:
            break

    if orderable_only:
        valid_products = []
        suppliers = Supplier.objects.enabled().filter(shops=request.shop)

        for product in products:
            # this instance should always exist as the listed() queryset uses the current shop as a filter
            shop_product = product.get_shop_instance(request.shop, allow_cache=True)

            for supplier in suppliers:
                if shop_product.is_orderable(supplier, request.customer, shop_product.minimum_purchase_quantity):
                    valid_products.append(product)
                    break

        products = valid_products

    products = cache_product_things(request, products)
    products = sorted(products, key=lambda p: product_ids.index(p.id))  # pragma: no branch
    return products


@contextfunction
def get_newest_products(context, n_products=6, orderable_only=True):
    request = context["request"]

    key, products = context_cache.get_cached_value(
        identifier="newest_products",
        item=cache_utils.get_newest_products_cache_item(request.shop),
        context=request,
        n_products=n_products, orderable_only=orderable_only
    )
    if products is not None:
        return products

    products = _get_listed_products(
        context,
        n_products,
        ordering="-pk",
        filter_dict={
            "variation_parent": None
        },
        orderable_only=orderable_only
    )
    products = cache_product_things(request, products)
    context_cache.set_cached_value(key, products, settings.SHUUP_TEMPLATE_HELPERS_CACHE_DURATION)
    return products


@contextfunction
def get_random_products(context, n_products=6, orderable_only=True):
    request = context["request"]
    key, products = context_cache.get_cached_value(
        identifier="random_products",
        item=cache_utils.get_random_products_cache_item(request.shop),
        context=request,
        n_products=n_products, orderable_only=orderable_only
    )
    if products is not None:
        return products

    products = _get_listed_products(
        context,
        n_products,
        ordering="?",
        filter_dict={
            "variation_parent": None
        },
        orderable_only=orderable_only
    )
    products = cache_product_things(request, products)
    context_cache.set_cached_value(key, products, settings.SHUUP_TEMPLATE_HELPERS_CACHE_DURATION)
    return products


@contextfunction
def get_products_for_categories(context, categories, n_products=6, orderable_only=True):
    request = context["request"]
    key, products = context_cache.get_cached_value(
        identifier="products_for_category",
        item=cache_utils.get_products_for_category_cache_item(request.shop),
        context=request,
        n_products=n_products,
        categories=categories,
        orderable_only=orderable_only
    )
    if products is not None:
        return products

    products = _get_listed_products(
        context,
        n_products,
        ordering="?",
        filter_dict={
            "variation_parent": None,
            "shop_products__categories__in": categories
        },
        orderable_only=orderable_only
    )
    products = cache_product_things(request, products)
    context_cache.set_cached_value(key, products, settings.SHUUP_TEMPLATE_HELPERS_CACHE_DURATION)
    return products


@contextfunction
def get_all_manufacturers(context):
    request = context["request"]
    key, manufacturers = context_cache.get_cached_value(
        identifier="all_manufacturers",
        item=cache_utils.get_all_manufacturers_cache_item(request.shop),
        context=request
    )
    if manufacturers is not None:
        return manufacturers

    products = Product.objects.listed(shop=request.shop, customer=request.customer)
    manufacturers_ids = products.values_list("manufacturer__id").distinct()
    manufacturers = Manufacturer.objects.filter(pk__in=manufacturers_ids)
    context_cache.set_cached_value(key, manufacturers, settings.SHUUP_TEMPLATE_HELPERS_CACHE_DURATION)
    return manufacturers


@contextfunction
def get_root_categories(context):
    request = context["request"]
    language = get_language()
    roots = get_cached_trees(
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
        requested_page = int(context["request"].GET.get("page") or 0)
    except ValueError:
        requested_page = 0
    current_page = min(max(requested_page, 1), paginator.num_pages)
    page = paginator.page(current_page)
    variables["page"] = page
    variables["page_range"] = _get_page_range(current_page, paginator.num_pages)
    variables["objects"] = page.object_list

    return variables


def _get_page_range(current_page, num_pages, range_gap=5):
    """
    Get page range around given page for a given number of pages.

    >>> list(_get_page_range(1, 10))
    [1, 2, 3, 4, 5]
    >>> list(_get_page_range(3, 10))
    [1, 2, 3, 4, 5]
    >>> list(_get_page_range(4, 10))
    [2, 3, 4, 5, 6]
    >>> list(_get_page_range(7, 10))
    [5, 6, 7, 8, 9]
    >>> list(_get_page_range(10, 10))
    [6, 7, 8, 9, 10]
    >>> list(_get_page_range(1, 1))
    [1]
    >>> list(_get_page_range(1, 4))
    [1, 2, 3, 4]
    >>> list(_get_page_range(3, 4))
    [1, 2, 3, 4]
    >>> list(_get_page_range(4, 4))
    [1, 2, 3, 4]
    """
    assert isinstance(num_pages, int)
    assert isinstance(current_page, int)
    assert num_pages >= 1
    assert current_page >= 1
    assert current_page <= num_pages

    max_start = max(num_pages - range_gap + 1, 1)
    start = min(max(current_page - (range_gap // 2), 1), max_start)
    end = min(start + range_gap - 1, num_pages)
    return six.moves.range(start, end + 1)


@contextfunction
def get_shop_language_choices(context):
    request = context["request"]
    return get_language_choices(request.shop)


@contextfunction
def is_shop_admin(context):
    return is_admin_user(context["request"])


@contextfunction
def is_company_registration_allowed(context, request=None):
    current_request = request or context["request"]  # From macros it doesn't seem to always pass context correctly
    return allow_company_registration(current_request.shop)


@contextfunction
def can_toggle_all_seeing(context):
    request = context["request"]
    if request.customer.is_anonymous or request.is_company_member:
        # Looks like the user is currently forcing anonymous or company
        # mode which means that the visibility limit can't be used since
        # 'is all seeing' is purely person contact feature.
        return False
    return getattr(request.user, "is_superuser", False)


@contextfunction
def get_admin_edit_url(context, intance_or_model):
    from shuup.admin.template_helpers.shuup_admin import model_url
    url = model_url(context, intance_or_model)
    if url:
        return dict(
            url=url,
            name=intance_or_model._meta.verbose_name.title(),
        )


@contextfunction
def get_powered_by_content(context):
    return settings.SHUUP_FRONT_POWERED_BY_CONTENT
