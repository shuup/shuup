# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf.urls import url

from shuup.xtheme.views.command import command_dispatch
from shuup.xtheme.views.editor import EditorView
from shuup.xtheme.views.extra import extra_view_dispatch
from shuup.xtheme.views.plugins import (
    get_category_products_highlight,
    get_product_cross_sell_highlight,
    get_product_highlight,
    get_prouduct_selections_highlight,
)

urlpatterns = [
    url(r"^xtheme/editor/$", EditorView.as_view(), name="xtheme_editor"),
    url(r"^xtheme/(?P<view>.+)/*$", extra_view_dispatch, name="xtheme_extra_view"),
    url(r"^xtheme/$", command_dispatch, name="xtheme"),
    url(
        r"^xtheme-prod-hl/(?P<plugin_type>.*)/(?P<cutoff_days>\d+)/(?P<count>\d+)/(?P<cache_timeout>\d+)/$",
        get_product_highlight,
        name="xtheme-product-highlight",
    ),
    url(
        r"""
            ^xtheme-prod-cross-sell-hl/
            (?P<product_id>.*)/(?P<relation_type>.*)/(?P<use_parents>\d+)/
            (?P<count>\d+)/(?P<cache_timeout>\d+)/$
        """.strip(),
        get_product_cross_sell_highlight,
        name="xtheme-product-cross-sells-highlight",
    ),
    url(
        r"^xtheme-cat-products-hl/(?P<category_id>\d+)/(?P<count>\d+)/(?P<cache_timeout>\d+)/$",
        get_category_products_highlight,
        name="xtheme-category-products-highlight",
    ),
    url(
        r"^xtheme-prod-selections-hl/(?P<product_ids>.*)/(?P<cache_timeout>\d+)/$",
        get_prouduct_selections_highlight,
        name="xtheme-product-selections-highlight",
    ),
]
