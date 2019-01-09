# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals, with_statement

import datetime

from django.db.models import Sum
from django.utils.translation import get_language

from shuup.core import cache
from shuup.core.models import OrderLine, OrderLineType, Product
from shuup.utils.dates import to_aware


def get_best_selling_product_info(shop_ids, cutoff_days=30):
    shop_ids = sorted(map(int, shop_ids))
    cutoff_date = datetime.date.today() - datetime.timedelta(days=cutoff_days)
    cache_key = "best_sellers:%r_%s" % (shop_ids, cutoff_date)
    sales_data = cache.get(cache_key)
    if sales_data is None:
        sales_data = (
            OrderLine.objects
            .filter(
                order__shop_id__in=shop_ids,
                order__order_date__gte=to_aware(cutoff_date),
                type=OrderLineType.PRODUCT
            )
            .values("product")
            .annotate(n=Sum("quantity"))
            .order_by("-n")[:100]
            .values_list("product", "product__variation_parent_id", "n")
        )
        cache.set(cache_key, sales_data, 3 * 60 * 60)  # three hours
    return sales_data


def get_products_ordered_with(prod, count=20, request=None, language=None):
    cache_key = "ordered_with:%d" % prod.pk
    product_ids = cache.get(cache_key)
    if product_ids is None:
        # XXX: could this be optimized more? (and does it matter?)
        order_ids = (
            OrderLine.objects.filter(product=prod, type=OrderLineType.PRODUCT)
            .values_list("order__id", flat=True)
        )
        product_ids = (
            OrderLine.objects
            .filter(order_id__in=order_ids)
            .exclude(product=prod)
            .distinct()
            .values_list("product", flat=True)
        )
        cache.set(cache_key, set(product_ids), 4 * 60 * 60)
    return (
        Product.objects
        .all_visible(request, language=language)
        .filter(id__in=product_ids)
        .order_by("?")[:count]
    )


def get_products_by_brand(prod, count=6, request=None, language=None):
    language = language or get_language()
    return list(
        Product.objects
        .all_visible(request, language)
        .filter(manufacturer_id__in=[prod.manufacturer_id])
        .exclude(pk=prod.id).order_by("?")[:count]
    )


def get_products_by_same_categories(prod, count=6, request=None, language=None):
    categories = prod.categories.values_list("pk", flat=True)
    language = language or get_language()
    return list(
        Product.objects
        .all_visible(request, language)
        .filter(categories__id__in=categories)
        .exclude(pk=prod.id).order_by("?")[:count]
    )
