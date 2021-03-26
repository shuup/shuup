# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import with_statement

from django.utils.translation import get_language

from shuup.core.models import Product, ProductAttribute
from shuup.utils.translation import cache_translations


def cache_product_things(request, products, language=None, attribute_identifiers=("author",)):
    # Cache necessary things for products. WARNING: This will cause queryset iteration.
    language = language or get_language()
    # TODO: Should we cache prices here?
    if attribute_identifiers:
        Product.cache_attributes_for_targets(
            ProductAttribute, products, attribute_identifiers=attribute_identifiers, language=language
        )
    products = cache_translations(products, (language,))
    return products
