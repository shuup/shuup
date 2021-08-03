# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.conf import settings
from django.core.paginator import Paginator
from django.middleware.csrf import get_token
from django.utils.translation import get_language
from jinja2.utils import contextfunction

from shuup.core.catalog import ProductCatalog, ProductCatalogContext
from shuup.core.models import Category, Manufacturer, ProductMode, ShopProductVisibility
from shuup.front.utils.companies import allow_company_registration
from shuup.front.utils.product_statistics import get_best_selling_product_info
from shuup.front.utils.translation import get_language_choices
from shuup.front.utils.user import is_admin_user
from shuup.front.utils.views import cache_product_things
from shuup.utils import django_compat
from shuup.utils.django_compat import reverse
from shuup.utils.importing import cached_load
from shuup.utils.mptt import get_cached_trees
from shuup.utils.translation import cache_translations_for_tree


def get_login_form(request, id_prefix="quick-login"):
    # Getting the form from the Login view
    form = cached_load("SHUUP_LOGIN_VIEW")(request=request).get_form(id_prefix=id_prefix)
    return form


def _get_listed_products(context, n_products, ordering=None, filter_dict=None, orderable_only=True, extra_filters=None):
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
    customer = getattr(request, "customer", None)
    shop = request.shop

    catalog = ProductCatalog(
        ProductCatalogContext(
            shop=shop,
            user=getattr(request, "user", None),
            contact=customer,
            purchasable_only=orderable_only,
            visibility=ShopProductVisibility.LISTED,
        )
    )

    if not filter_dict:
        filter_dict = {}

    products_qs = (
        catalog.get_products_queryset()
        .language(get_language())
        .filter(mode__in=ProductMode.get_parent_modes(), **filter_dict)
    )

    if extra_filters:
        products_qs = products_qs.filter(extra_filters)

    if ordering:
        products_qs = products_qs.order_by(ordering)

    return products_qs.distinct()[:n_products]


@contextfunction
def get_listed_products(context, n_products, ordering=None, filter_dict=None, orderable_only=True, extra_filters=None):
    """
    A cached version of _get_listed_products
    """
    request = context["request"]
    products = _get_listed_products(
        context,
        n_products,
        ordering=ordering,
        filter_dict=filter_dict,
        orderable_only=orderable_only,
        extra_filters=extra_filters,
    )
    products = cache_product_things(request, products)
    return products


@contextfunction
def get_best_selling_products(context, n_products=12, cutoff_days=30, orderable_only=True, supplier=None):
    request = context["request"]
    products = _get_best_selling_products(cutoff_days, n_products, orderable_only, request, supplier=supplier)
    return products


def _get_best_selling_products(cutoff_days, n_products, orderable_only, request, supplier=None):
    data = get_best_selling_product_info(
        shop_ids=[request.shop.pk],
        cutoff_days=cutoff_days,
        supplier=supplier,
        orderable_only=orderable_only,
        quantity=n_products,
    )
    sorted_product_ids = sorted(data, key=lambda item: item[1], reverse=True)
    product_ids = [item[0] for item in sorted_product_ids]

    catalog = ProductCatalog(
        ProductCatalogContext(
            shop=request.shop,
            user=getattr(request, "user", None),
            supplier=supplier,
            contact=getattr(request, "customer", None),
            purchasable_only=orderable_only,
            visibility=ShopProductVisibility.LISTED,
        )
    )
    valid_products_qs = (
        catalog.get_products_queryset()
        .filter(id__in=product_ids, mode__in=ProductMode.get_parent_modes())
        .distinct()[:n_products]
    )

    products = cache_product_things(request, valid_products_qs)
    # order products by the best selling order
    products = sorted(products, key=lambda product: product_ids.index(product.pk))
    return products


@contextfunction
def get_newest_products(context, n_products=6, orderable_only=True):
    request = context["request"]
    products = _get_listed_products(
        context, n_products, ordering="-pk", filter_dict={"variation_parent": None}, orderable_only=orderable_only
    )
    products = cache_product_things(request, products)
    return products


@contextfunction
def get_random_products(context, n_products=6, orderable_only=True):
    request = context["request"]
    products = _get_listed_products(
        context, n_products, ordering="?", filter_dict={"variation_parent": None}, orderable_only=orderable_only
    )
    products = cache_product_things(request, products)
    return products


@contextfunction
def get_products_for_categories(context, categories, n_products=6, orderable_only=True):
    request = context["request"]
    products = _get_listed_products(
        context,
        n_products,
        ordering="?",
        filter_dict={"variation_parent": None, "shop_products__categories__in": categories},
        orderable_only=orderable_only,
    )
    products = cache_product_things(request, products)
    return products


@contextfunction
def get_all_manufacturers(context, purchasable_only=False):
    request = context["request"]
    catalog = ProductCatalog(
        ProductCatalogContext(
            shop=request.shop,
            user=getattr(request, "user", None),
            contact=getattr(request, "customer", None),
            purchasable_only=purchasable_only,
            visibility=ShopProductVisibility.LISTED,
        )
    )
    manufacturers = Manufacturer.objects.filter(
        pk__in=catalog.get_products_queryset().values_list("manufacturer_id", flat=True).distinct()
    )
    return manufacturers


@contextfunction
def get_root_categories(context):
    request = context["request"]
    language = get_language()
    roots = get_cached_trees(
        Category.objects.all_visible(customer=request.customer, shop=request.shop, language=language)
    )
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
    variables["is_paginated"] = paginator.num_pages > 1
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


@contextfunction
def get_config(context):
    request = context["request"]
    is_authenticated = request.user.is_authenticated
    return {
        "uploadUrl": (reverse("shuup:media-upload") if is_authenticated else None),
        "csrf": get_token(request),
    }


def is_authenticated(user):
    return django_compat.is_authenticated(user)
