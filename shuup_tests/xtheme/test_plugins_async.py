# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.core.models import CategoryStatus, ProductCrossSell, ProductCrossSellType
from shuup.testing.factories import (
    CategoryFactory,
    create_product,
    get_default_category,
    get_default_shop,
    get_default_supplier,
)
from shuup.testing.utils import apply_request_middleware
from shuup.xtheme._theme import get_current_theme, override_current_theme_class
from shuup.xtheme.layout import LayoutCell
from shuup.xtheme.plugins.products_async import (
    HighlightType,
    ProductCrossSellsPlugin,
    ProductHighlightPlugin,
    ProductSelectionPlugin,
    ProductsFromCategoryPlugin,
)
from shuup.xtheme.views.forms import LayoutCellFormGroup
from shuup_tests.front.fixtures import get_jinja_context
from shuup_tests.utils import SmartClient


def get_context(rf, customer=None, product=None, is_ajax=True):
    request = rf.get("/")
    request.shop = get_default_shop()
    apply_request_middleware(request)
    if customer:
        request.customer = customer

    if is_ajax:
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"
    vars = {"request": request}
    if product:
        vars.update({"product": product})

    if is_ajax:
        assert request.is_ajax()
    return get_jinja_context(**vars)


def check_expected_product_count(url, expected_count):
    client = SmartClient(HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    response, soup = client.response_and_soup(url)
    assert response.status_code == 200
    assert len(soup.findAll("div", {"class": "product-box"})) == expected_count


@pytest.mark.parametrize(
    "highlight_type,",
    [
        (HighlightType.NEWEST.value),
        (HighlightType.RANDOM.value),
        (HighlightType.NEWEST.value),
        (HighlightType.RANDOM.value),
        (HighlightType.BEST_SELLING.value),
        ("notvalid_type"),
    ],
)
@pytest.mark.django_db
def test_product_hightlight_plugin(rf, highlight_type, reindex_catalog):
    shop = get_default_shop()
    supplier = get_default_supplier()
    p1 = create_product("p1", shop, supplier, "10")
    p2 = create_product("p2", shop, supplier, "20")
    p3 = create_product("p3", shop, supplier, "30")
    p4 = create_product("p4", shop, supplier, "40")

    sp4 = p4.get_shop_instance(shop)
    sp4.purchasable = False
    sp4.save()

    reindex_catalog()

    plugin = ProductHighlightPlugin({"type": highlight_type, "count": 4, "cache_timeout": 120})
    plugin_context = plugin.get_context_data(get_context(rf, is_ajax=False))
    context_products = plugin_context["products"]

    assert len(context_products) == 0

    plugin_context = plugin.get_context_data(get_context(rf))
    context_data_url = plugin_context["data_url"]
    context_products = plugin_context["products"]
    if highlight_type in [HighlightType.BEST_SELLING.value, "notvalid_type"]:
        assert len(context_products) == 0
    else:
        assert p1 in context_products
        assert p2 in context_products
        assert p3 in context_products
        assert p4 in context_products

        check_expected_product_count(context_data_url, 4)
        check_expected_product_count(context_data_url, 4)  # one for checking it is cached


@pytest.mark.django_db
def test_product_selection_plugin(rf, reindex_catalog):
    shop = get_default_shop()
    supplier = get_default_supplier()
    p1 = create_product("p1", shop, supplier, "10")
    p2 = create_product("p2", shop, supplier, "20")
    p3 = create_product("p3", shop, supplier, "30")
    p4 = create_product("p4", shop, supplier, "40")

    sp1 = p1.get_shop_instance(shop)
    sp2 = p2.get_shop_instance(shop)
    sp3 = p3.get_shop_instance(shop)

    reindex_catalog()
    plugin = ProductSelectionPlugin(
        {"products": [sp1.product.pk, sp2.product.pk, sp3.product.pk], "cache_timeout": 120}
    )
    plugin_context = plugin.get_context_data(get_context(rf, is_ajax=False))
    context_products = plugin_context["products"]

    assert len(context_products) == 0

    plugin_context = plugin.get_context_data(get_context(rf))
    context_data_url = plugin_context["data_url"]
    context_products = plugin_context["products"]
    assert p1 in context_products
    assert p2 in context_products
    assert p3 in context_products
    assert p4 not in context_products

    check_expected_product_count(context_data_url, 3)
    check_expected_product_count(context_data_url, 3)  # one for checking it is cached

    # test the plugin form
    with override_current_theme_class(None):
        theme = get_current_theme(get_default_shop())
        cell = LayoutCell(theme, ProductSelectionPlugin.identifier, sizes={"md": 8})
        lcfg = LayoutCellFormGroup(layout_cell=cell, theme=theme, request=apply_request_middleware(rf.get("/")))
        # not valid, products are required
        assert not lcfg.is_valid()

        lcfg = LayoutCellFormGroup(
            data={
                "general-cell_width": "8",
                "general-cell_align": "pull-right",
                "plugin-products": [p1.pk, p2.pk],
                "plugin-cache_timeout": 120,
            },
            layout_cell=cell,
            theme=theme,
            request=apply_request_middleware(rf.get("/")),
        )
        assert lcfg.is_valid()
        lcfg.save()
        assert cell.config["products"] == [str(p1.pk), str(p2.pk)]


@pytest.mark.django_db
def test_product_from_category_plugin(rf, reindex_catalog):
    shop = get_default_shop()
    category1 = get_default_category()
    category2 = CategoryFactory(status=CategoryStatus.VISIBLE)

    category1.shops.add(shop)
    category2.shops.add(shop)

    p1 = create_product("p1", shop, get_default_supplier(), "10")
    p2 = create_product("p2", shop, get_default_supplier(), "20")
    p3 = create_product("p3", shop, get_default_supplier(), "30")

    sp1 = p1.get_shop_instance(shop)
    sp2 = p2.get_shop_instance(shop)
    sp3 = p3.get_shop_instance(shop)

    sp1.categories.add(category1)
    sp2.categories.add(category1)
    sp3.categories.add(category2)

    reindex_catalog()
    plugin = ProductsFromCategoryPlugin({"category": category1.pk, "cache_timeout": 120})
    plugin_context = plugin.get_context_data(get_context(rf, is_ajax=False))
    context_products = plugin_context["products"]

    assert len(context_products) == 0

    plugin_context = plugin.get_context_data(get_context(rf))
    context_data_url = plugin_context["data_url"]
    context_products = plugin_context["products"]
    assert p1 in context_products
    assert p2 in context_products
    assert p3 not in context_products

    check_expected_product_count(context_data_url, 2)
    check_expected_product_count(context_data_url, 2)  # one for checking it is cached

    # test the plugin form
    with override_current_theme_class(None):
        theme = get_current_theme(get_default_shop())
        cell = LayoutCell(theme, ProductsFromCategoryPlugin.identifier, sizes={"md": 8})
        lcfg = LayoutCellFormGroup(layout_cell=cell, theme=theme, request=apply_request_middleware(rf.get("/")))
        assert not lcfg.is_valid()

        lcfg = LayoutCellFormGroup(
            data={
                "general-cell_width": "8",
                "general-cell_align": "pull-right",
                "plugin-count": 4,
                "plugin-category": category2.pk,
                "plugin-cache_timeout": 3600,
            },
            layout_cell=cell,
            theme=theme,
            request=apply_request_middleware(rf.get("/")),
        )
        assert lcfg.is_valid()
        lcfg.save()
        assert cell.config["category"] == str(category2.pk)


@pytest.mark.django_db
def test_cross_sell_plugin_renders(rf, reindex_catalog):
    """
    Test that the plugin renders a product
    """
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product("test-sku", shop=shop, supplier=supplier)
    computed = create_product("test-computed-sku", shop=shop, supplier=supplier)
    reindex_catalog()

    type = ProductCrossSellType.COMPUTED

    ProductCrossSell.objects.create(product1=product, product2=computed, type=type)
    assert ProductCrossSell.objects.filter(product1=product, type=type).count() == 1

    context = get_context(rf, product=product)
    rendered = ProductCrossSellsPlugin({"type": type}).render(context)
    assert computed.sku in rendered

    plugin = ProductCrossSellsPlugin({"type": type, "cache_timeout": 120})
    plugin_context = plugin.get_context_data(get_context(rf, product=product))
    context_data_url = plugin_context["data_url"]
    check_expected_product_count(context_data_url, 1)
    check_expected_product_count(context_data_url, 1)  # one for checking it is cached


@pytest.mark.django_db
def test_cross_sell_plugin_accepts_initial_config_as_string_or_enum():
    plugin = ProductCrossSellsPlugin({"type": "computed"})
    assert plugin.config["type"] == ProductCrossSellType.COMPUTED

    plugin = ProductCrossSellsPlugin({"type": ProductCrossSellType.RECOMMENDED})
    assert plugin.config["type"] == ProductCrossSellType.RECOMMENDED


@pytest.mark.django_db
def test_cross_sell_plugin_with_invalid_type(rf):
    plugin = ProductCrossSellsPlugin({"type": "foobar"})
    assert plugin.config["type"] == ProductCrossSellType.RELATED

    context = get_context(rf)
    plugin.config["type"] = "foobar"
    context_data = plugin.get_context_data({"request": context["request"]})
    assert context_data["data_url"] == "/"


@pytest.mark.django_db
def test_cross_sell_plugin_with_invalid_type_2(rf):
    plugin = ProductCrossSellsPlugin({"type": None})
    assert plugin.config["type"] is None

    context = get_context(rf)
    context_data = plugin.get_context_data({"request": context["request"]})
    assert context_data["data_url"] == "/"


@pytest.mark.django_db
def test_cross_sell_plugin_with_product_that_does_not_exists(rf):
    plugin = ProductCrossSellsPlugin({"type": None})
    assert plugin.config["type"] is None

    context = get_context(rf)
    plugin.config["product"] = "1111"
    context_data = plugin.get_context_data({"request": context["request"]})
    assert context_data["data_url"] == "/"
