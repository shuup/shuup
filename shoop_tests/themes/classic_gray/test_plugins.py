# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shoop.core.models import Product, ProductCrossSell, StockBehavior
from shoop.testing.factories import create_product, get_default_shop
from shoop.themes.classic_gray.plugins import ProductCrossSellsPlugin
from shoop_tests.front.fixtures import get_jinja_context


@pytest.mark.django_db
def test_cross_sell_plugin_renders():
    """
    Test that the plugin renders a product
    """
    shop = get_default_shop()
    product = create_product("test-sku", shop=shop, stock_behavior=StockBehavior.UNSTOCKED)
    computed = create_product("test-computed-sku", shop=shop, stock_behavior=StockBehavior.UNSTOCKED)
    type ="computed"

    ProductCrossSell.objects.create(product1=product, product2=computed, type=type)
    assert ProductCrossSell.objects.filter(product1=product, type=type).count() == 1

    context = get_jinja_context(product=product)
    rendered  = ProductCrossSellsPlugin({"type": type}).render(context)
    assert computed.sku in rendered
