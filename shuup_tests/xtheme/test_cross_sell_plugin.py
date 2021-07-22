# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.core.models import ProductCrossSell, ProductCrossSellType
from shuup.testing.factories import create_product, get_default_shop, get_default_supplier
from shuup.xtheme.plugins.products import ProductCrossSellsPlugin
from shuup_tests.front.fixtures import get_jinja_context


@pytest.mark.django_db
def test_cross_sell_plugin_renders(reindex_catalog):
    """
    Test that the plugin renders a product
    """
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product("test-sku", shop=shop, supplier=supplier)
    computed = create_product("test-computed-sku", shop=shop, supplier=supplier)
    type = ProductCrossSellType.COMPUTED
    reindex_catalog()

    ProductCrossSell.objects.create(product1=product, product2=computed, type=type)
    assert ProductCrossSell.objects.filter(product1=product, type=type).count() == 1

    context = get_jinja_context(product=product)
    rendered = ProductCrossSellsPlugin({"type": type}).render(context)
    assert computed.sku in rendered


@pytest.mark.django_db
def test_cross_sell_plugin_accepts_initial_config_as_string_or_enum():
    plugin = ProductCrossSellsPlugin({"type": "computed"})
    assert plugin.config["type"] == ProductCrossSellType.COMPUTED

    plugin = ProductCrossSellsPlugin({"type": ProductCrossSellType.RECOMMENDED})
    assert plugin.config["type"] == ProductCrossSellType.RECOMMENDED


@pytest.mark.django_db
def test_cross_sell_plugin_with_invalid_type():
    plugin = ProductCrossSellsPlugin({"type": "foobar"})
    assert plugin.config["type"] == ProductCrossSellType.RELATED

    plugin.config["type"] = "foobar"
    context_data = plugin.get_context_data({"request": "REQUEST"})
    assert context_data["type"] == ProductCrossSellType.RELATED
