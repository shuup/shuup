# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from collections import OrderedDict

import six
from django.utils.translation import get_language

from shuup.core.models import (
    AttributeVisibility, ProductMode, ProductVariationResult
)
from shuup.front.utils.views import cache_product_things
from shuup.utils.numbers import get_string_sort_order


def get_product_context(request, product, language=None):
    """
    Get product context

    Used in `shuup.front.views.product:ProductDetailView`

    :return: A context dict containing everything needed to render product view
    :rtype: dict
    """

    if not language:
        language = get_language()

    shop_product = product.get_shop_instance(request.shop)
    context = {}
    context["product"] = product
    context["category"] = shop_product.primary_category
    context["orderability_errors"] = list(shop_product.get_orderability_errors(
        supplier=None, quantity=1, customer=request.customer, ignore_minimum=True))
    context["variation_children"] = []
    if product.mode == ProductMode.SIMPLE_VARIATION_PARENT:
        context["variation_children"] = cache_product_things(
            request,
            sorted(
                product.variation_children.language(language).all(),
                key=lambda p: get_string_sort_order(p.variation_name or p.name)
            )
        )
        context["orderable_variation_children"] = [
            p for p in context["variation_children"]
            if p.get_shop_instance(request.shop).is_orderable(supplier=None, customer=request.customer, quantity=1)
        ]
    elif product.mode == ProductMode.VARIABLE_VARIATION_PARENT:
        variation_variables = product.variation_variables.all().prefetch_related("values")
        orderable_children, is_orderable = get_orderable_variation_children(product, request, variation_variables)
        context["orderable_variation_children"] = orderable_children
        context["variation_orderable"] = is_orderable
        context["variation_variables"] = variation_variables
    elif product.mode == ProductMode.PACKAGE_PARENT:
        children = product.get_all_package_children().translated().order_by("translations__name")
        context["package_children"] = cache_product_things(request, children)

    context["shop_product"] = shop_product
    context["attributes"] = product.attributes.filter(
        attribute__visibility_mode=AttributeVisibility.SHOW_ON_PRODUCT_PAGE)
    context["primary_image"] = shop_product.public_primary_image
    context["images"] = shop_product.public_images
    return context


def get_orderable_variation_children(product, request, variation_variables):
    if not variation_variables:
        variation_variables = product.variation_variables.all().prefetch_related("values")
    orderable_variation_children = OrderedDict()
    orderable = 0
    for combo_data in product.get_all_available_combinations():
        combo = combo_data["variable_to_value"]
        for k, v in six.iteritems(combo):
            if k not in orderable_variation_children:
                orderable_variation_children[k] = set()

        res = ProductVariationResult.resolve(product, combo)
        if res and res.get_shop_instance(request.shop).is_orderable(
                supplier=None,
                customer=request.customer,
                quantity=1
        ):
            orderable += 1

            for k, v in six.iteritems(combo):
                orderable_variation_children[k].add(v)

    return (orderable_variation_children, orderable != 0)
