# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.core.exceptions import ValidationError
from filer.models import File

from shuup.core.models import CategoryStatus, CategoryVisibility
from shuup.testing.factories import (
    create_random_person, get_default_category, get_default_customer_group,
    get_default_shop
)
from shuup.testing.utils import apply_request_middleware
from shuup.xtheme import resources
from shuup.xtheme.plugins.category_links import CategoryLinksPlugin
from shuup.xtheme.plugins.image import ImageIDField, ImagePluginChoiceWidget
from shuup.xtheme.plugins.snippets import SnippetsPlugin
from shuup.xtheme.plugins.social_media_links import SocialMediaLinksPlugin
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
    context = get_jinja_context()
    icon_classes = SocialMediaLinksPlugin.icon_classes
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
    image = File.objects.create()
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
    assert widget.get_object(1000) == None
