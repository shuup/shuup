# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.core.exceptions import ValidationError
from filer.models import File

from shuup.core.models import CategoryStatus, CategoryVisibility
from shuup.testing.factories import (
    CategoryFactory,
    create_product,
    create_random_person,
    get_default_category,
    get_default_customer_group,
    get_default_shop,
    get_default_supplier,
)
from shuup.testing.utils import apply_request_middleware
from shuup.xtheme import resources
from shuup.xtheme._theme import get_current_theme, override_current_theme_class
from shuup.xtheme.layout import LayoutCell
from shuup.xtheme.plugins.category_links import CategoryLinksPlugin
from shuup.xtheme.plugins.image import ImageIDField, ImagePluginChoiceWidget
from shuup.xtheme.plugins.products import (
    HighlightType,
    ProductHighlightPlugin,
    ProductSelectionPlugin,
    ProductsFromCategoryPlugin,
)
from shuup.xtheme.plugins.snippets import SnippetsPlugin
from shuup.xtheme.plugins.social_media_links import SocialMediaLinksPlugin
from shuup.xtheme.views.forms import LayoutCellFormGroup
from shuup_tests.front.fixtures import get_jinja_context


def test_snippets_plugin():
    resources_name = resources.RESOURCE_CONTAINER_VAR_NAME
    context = {
        resources_name: resources.ResourceContainer(),
    }
    config = {
        "in_place": "This is in place",
        "head_end": "This the head end",
        "body_start": "This is the body start",
        "body_end": "This is the body end",
    }
    plugin = SnippetsPlugin(config)
    rendered = plugin.render(context)
    # Make sure that plugin properly rendered in-place stuff
    assert config.pop("in_place") == rendered

    # Make sure all of the resources were added to context
    resource_dict = context[resources_name].resources
    for location, snippet in config.items():
        assert snippet == resource_dict[location][0]


@pytest.mark.django_db
def test_social_media_plugin_ordering():
    """
    Test that social media plugin ordering works as expected
    """
    link_1_type = "Facebook"
    link_1 = {
        "url": "http://www.facebook.com",
        "ordering": 2,
    }

    link_2_type = "Twitter"
    link_2 = {
        "url": "http://www.twitter.com",
        "ordering": 1,
    }

    links = {
        link_1_type: link_1,
        link_2_type: link_2,
    }
    plugin = SocialMediaLinksPlugin({"links": links})
    assert len(plugin.get_links()) == 2

    # Make sure link 2 comes first
    assert plugin.get_links()[0][2] == link_2["url"]


def get_context(rf, customer=None):
    request = rf.get("/")
    request.shop = get_default_shop()
    apply_request_middleware(request)
    if customer:
        request.customer = customer
    vars = {"request": request}
    return get_jinja_context(**vars)


@pytest.mark.django_db
def test_category_links_plugin(rf):
    """
    Test that the plugin only displays visible categories
    with shop (since we can't have a request without shop
    or customer)
    """
    category = get_default_category()
    category.shops.clear()
    context = get_context(rf)
    plugin = CategoryLinksPlugin({"show_all_categories": True})
    assert context["request"].customer.is_anonymous
    assert category not in plugin.get_context_data(context)["categories"]

    category.status = CategoryStatus.VISIBLE
    category.shops.add(get_default_shop())
    category.save()
    assert context["request"].customer.is_anonymous
    assert context["request"].shop in category.shops.all()
    assert category in plugin.get_context_data(context)["categories"]


@pytest.mark.django_db
@pytest.mark.parametrize("show_all_categories", [True, False])
def test_category_links_plugin_with_customer(rf, show_all_categories):
    """
    Test plugin for categories that is visible for certain group
    """
    shop = get_default_shop()
    group = get_default_customer_group()
    customer = create_random_person()
    customer.groups.add(group)
    customer.save()

    request = rf.get("/")
    request.shop = get_default_shop()
    apply_request_middleware(request)
    request.customer = customer

    category = get_default_category()
    category.status = CategoryStatus.VISIBLE
    category.visibility = CategoryVisibility.VISIBLE_TO_GROUPS
    category.visibility_groups.add(group)
    category.shops.add(shop)
    category.save()

    vars = {"request": request}
    context = get_jinja_context(**vars)
    plugin = CategoryLinksPlugin({"categories": [category.pk], "show_all_categories": show_all_categories})
    assert category.is_visible(customer)
    assert category in plugin.get_context_data(context)["categories"]

    customer_without_groups = create_random_person()
    customer_without_groups.groups.clear()

    assert not category.is_visible(customer_without_groups)
    request.customer = customer_without_groups
    context = get_jinja_context(**vars)
    assert category not in plugin.get_context_data(context)["categories"]


@pytest.mark.django_db
def test_category_links_plugin_show_all(rf):
    """
    Test that show_all_categories forces plugin to return all visible categories
    """
    category = get_default_category()
    category.status = CategoryStatus.VISIBLE
    category.shops.add(get_default_shop())
    category.save()
    context = get_context(rf)
    plugin = CategoryLinksPlugin({"show_all_categories": False})
    assert context["request"].customer.is_anonymous
    assert context["request"].shop in category.shops.all()
    assert not plugin.get_context_data(context)["categories"]

    plugin = CategoryLinksPlugin({"show_all_categories": True})
    assert category in plugin.get_context_data(context)["categories"]


@pytest.mark.django_db
def test_plugin_image_id_field():
    """
    Test that ImageIDField only accepts ID values. We're not necessarily testing
    that the ID value is a valid File
    """
    File.objects.create()
    image_id = ImageIDField()
    assert image_id.clean("1") == 1

    with pytest.raises(ValidationError):
        image_id.clean("something malicious")


@pytest.mark.django_db
def test_image_plugin_choice_widget_get_object():
    """
    Test get_object method for ImagePluginChoiceWidget
    """
    image = File.objects.create()
    widget = ImagePluginChoiceWidget()
    # Make sure that widget returns valid image instance
    assert widget.get_object(image.pk) == image

    # We don't want any exceptions if the image doesn't exist or else we won't be
    # able to display the form to change it
    assert widget.get_object(1000) is None


@pytest.mark.django_db
def test_product_selection_plugin_v1(rf, reindex_catalog):
    shop = get_default_shop()
    p1 = create_product("p1", shop, get_default_supplier(), "10")
    p2 = create_product("p2", shop, get_default_supplier(), "20")
    p3 = create_product("p3", shop, get_default_supplier(), "30")
    p4 = create_product("p4", shop, get_default_supplier(), "40")

    sp1 = p1.get_shop_instance(shop)
    sp2 = p2.get_shop_instance(shop)
    sp3 = p3.get_shop_instance(shop)

    reindex_catalog()
    context = get_context(rf)

    plugin = ProductSelectionPlugin({"products": [sp1.product.pk, sp2.product.pk, sp3.product.pk]})
    context_products = plugin.get_context_data(context)["products"]
    assert p1 in context_products
    assert p2 in context_products
    assert p3 in context_products
    assert p4 not in context_products

    # test the plugin form
    with override_current_theme_class(None):
        theme = get_current_theme(get_default_shop())
        cell = LayoutCell(theme, ProductSelectionPlugin.identifier, sizes={"md": 8})
        lcfg = LayoutCellFormGroup(layout_cell=cell, theme=theme, request=apply_request_middleware(rf.get("/")))
        # not valid, products are required
        assert not lcfg.is_valid()

        lcfg = LayoutCellFormGroup(
            data={"general-cell_width": "8", "general-cell_align": "pull-right", "plugin-products": [p1.pk, p2.pk]},
            layout_cell=cell,
            theme=theme,
            request=apply_request_middleware(rf.get("/")),
        )
        assert lcfg.is_valid()
        lcfg.save()
        assert cell.config["products"] == [str(p1.pk), str(p2.pk)]


@pytest.mark.parametrize(
    "highlight_type,orderable",
    [
        (HighlightType.NEWEST.value, True),
        (HighlightType.RANDOM.value, True),
        (HighlightType.NEWEST.value, False),
        (HighlightType.RANDOM.value, False),
    ],
)
@pytest.mark.django_db
def test_product_hightlight_plugin(rf, highlight_type, orderable, reindex_catalog):
    shop = get_default_shop()
    p1 = create_product("p1", shop, get_default_supplier(), "10")
    p2 = create_product("p2", shop, get_default_supplier(), "20")
    p3 = create_product("p3", shop, get_default_supplier(), "30")
    p4 = create_product("p4", shop, get_default_supplier(), "40")

    sp4 = p4.get_shop_instance(shop)
    sp4.purchasable = False
    sp4.save()

    context = get_context(rf)
    plugin = ProductHighlightPlugin({"type": highlight_type, "count": 4, "orderable_only": orderable})
    reindex_catalog()
    context_products = plugin.get_context_data(context)["products"]

    assert p1 in context_products
    assert p2 in context_products
    assert p3 in context_products
    if orderable:
        assert p4 not in context_products
    else:
        assert p4 in context_products


@pytest.mark.django_db
def test_product_selection_plugin_v2(rf, reindex_catalog):
    shop = get_default_shop()
    p1 = create_product("p1", shop, get_default_supplier(), "10")
    p2 = create_product("p2", shop, get_default_supplier(), "20")
    p3 = create_product("p3", shop, get_default_supplier(), "30")
    p4 = create_product("p4", shop, get_default_supplier(), "40")

    sp1 = p1.get_shop_instance(shop)
    sp2 = p2.get_shop_instance(shop)
    sp3 = p3.get_shop_instance(shop)

    reindex_catalog()
    context = get_context(rf)
    plugin = ProductSelectionPlugin({"products": [sp1.product.pk, sp2.product.pk, sp3.product.pk]})
    context_products = plugin.get_context_data(context)["products"]
    assert p1 in context_products
    assert p2 in context_products
    assert p3 in context_products
    assert p4 not in context_products

    # test the plugin form
    with override_current_theme_class(None):
        theme = get_current_theme(get_default_shop())
        cell = LayoutCell(theme, ProductSelectionPlugin.identifier, sizes={"md": 8})
        lcfg = LayoutCellFormGroup(layout_cell=cell, theme=theme, request=apply_request_middleware(rf.get("/")))
        # not valid, products are required
        assert not lcfg.is_valid()

        lcfg = LayoutCellFormGroup(
            data={"general-cell_width": "8", "general-cell_align": "pull-right", "plugin-products": [p1.pk, p2.pk]},
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
    context = get_context(rf)
    plugin = ProductsFromCategoryPlugin({"category": category1.pk})
    context_products = plugin.get_context_data(context)["products"]
    assert p1 in context_products
    assert p2 in context_products
    assert p3 not in context_products

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
            },
            layout_cell=cell,
            theme=theme,
            request=apply_request_middleware(rf.get("/")),
        )
        assert lcfg.is_valid()
        lcfg.save()
        assert cell.config["category"] == str(category2.pk)
