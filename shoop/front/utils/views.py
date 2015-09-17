# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import with_statement

from django.conf import settings
from django.core.paginator import Paginator
from django.utils.translation import get_language

from shoop.core.models import Product, ProductAttribute
from shoop.utils.translation import cache_translations


def cache_product_things(request, products, language=None, attribute_identifiers=("author",)):
    # Cache necessary things for products. WARNING: This will cause queryset iteration.
    language = language or get_language()
    # TODO: Should we cache prices here?
    if attribute_identifiers:
        Product.cache_attributes_for_targets(
            ProductAttribute, products,
            attribute_identifiers=attribute_identifiers,
            language=language)
    products = cache_translations(products, (language,))
    return products


def get_pagination_variables(request, products):
    """
    Used to update pagination variables to category view context
    """
    context = {}

    limit = getattr(settings, "SHOOP_PRODUCTLIST_PRODUCT_COUNT", None)
    if not limit:
        return context
    if len(products):
        context["paginator"] = paginator = Paginator(products, limit)
        if paginator.num_pages > 1:
            context["is_paginated"] = True
            try:
                context["page"] = page = paginator.page(request.GET.get("page") or 1)
                context["products"] = page.object_list
            except:
                pass
        else:
            context["is_paginated"] = False
    else:
        context["is_paginated"] = False
        context["paginator"] = None

    return context
