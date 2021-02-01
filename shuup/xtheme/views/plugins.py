# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.http import HttpResponse

from shuup.core.utils import context_cache
from shuup.xtheme.plugins.products_async import (
    ProductCrossSellsPlugin, ProductHighlightPlugin, ProductSelectionPlugin,
    ProductsFromCategoryPlugin
)

PRODUCT_HIGHLIGHT_CACHE_KEY_PREFIX = "shuup_xtheme_proudct_highlight_cache_key_%(shop_id)s"


def get_category_products_highlight(request, category_id, count, cache_timeout):
    key, html = context_cache.get_cached_value(
        identifier="xtheme_category_proudcts_highlights",
        item=PRODUCT_HIGHLIGHT_CACHE_KEY_PREFIX % {"shop_id": request.shop.pk},
        context=request,
        category_id=category_id,
        count=count,
        cache_timeout=cache_timeout
    )
    if html is not None:
        return HttpResponse(html)

    plugin = ProductsFromCategoryPlugin(
        config={
            "category": int(category_id),
            "count": int(count),
            "cache_timeout": int(cache_timeout)
        }
    )
    html = plugin.render(dict(request=request))
    context_cache.set_cached_value(key, html, int(cache_timeout))
    return HttpResponse(html)


def get_product_cross_sell_highlight(request, product_id, relation_type, use_parents, count, cache_timeout):
    key, html = context_cache.get_cached_value(
        identifier="xtheme_product_cross_sell_highlight",
        item=PRODUCT_HIGHLIGHT_CACHE_KEY_PREFIX % {"shop_id": request.shop.pk},
        context=request,
        product_id=product_id,
        type=relation_type,
        use_variation_parents=use_parents,
        count=count,
        cache_timeout=cache_timeout
    )
    if html is not None:
        return HttpResponse(html)

    plugin = ProductCrossSellsPlugin(
        config={
            "product": int(product_id),
            "type": relation_type,
            "use_variation_parents": bool(use_parents),
            "count": int(count),
            "cache_timeout": int(cache_timeout)
        }
    )
    html = plugin.render(dict(request=request))
    context_cache.set_cached_value(key, html, int(cache_timeout))
    return HttpResponse(html)


def get_product_highlight(request, plugin_type, cutoff_days, count, cache_timeout):
    key, html = context_cache.get_cached_value(
        identifier="xtheme_category_proudcts_highlights",
        item=PRODUCT_HIGHLIGHT_CACHE_KEY_PREFIX % {"shop_id": request.shop.pk},
        context=request,
        plugin_type=plugin_type,
        cutoff_days=cutoff_days,
        count=count,
        cache_timeout=cache_timeout
    )
    if html is not None:
        return HttpResponse(html)

    plugin = ProductHighlightPlugin(
        config={
            "type": plugin_type,
            "cutoff_days": int(cutoff_days),
            "count": int(count),
            "cache_timeout": int(cache_timeout)
        }
    )
    html = plugin.render(dict(request=request))
    context_cache.set_cached_value(key, html, int(cache_timeout))
    return HttpResponse(html)


def get_prouduct_selections_highlight(request, product_ids, cache_timeout):
    key, html = context_cache.get_cached_value(
        identifier="xtheme_category_proudcts_highlights",
        item=PRODUCT_HIGHLIGHT_CACHE_KEY_PREFIX % {"shop_id": request.shop.pk},
        context=request,
        plugin_type=product_ids,
        cache_timeout=cache_timeout
    )
    if html is not None:
        return HttpResponse(html)

    plugin = ProductSelectionPlugin(
        config={
            "products": [prod_id for prod_id in product_ids.split(",")],
            "cache_timeout": int(cache_timeout)
        }
    )
    html = plugin.render(dict(request=request))
    context_cache.set_cached_value(key, html, int(cache_timeout))
    return HttpResponse(html)
