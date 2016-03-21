# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shoop.core.models import CategoryStatus
from shoop.testing.factories import get_default_category
from shoop.xtheme import resources
from shoop.xtheme.plugins.category_links import CategoryLinksPlugin
from shoop.xtheme.plugins.snippets import SnippetsPlugin
from shoop.xtheme.plugins.social_media_links import SocialMediaLinksPlugin
from shoop_tests.front.fixtures import get_jinja_context


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


@pytest.mark.django_db
def test_category_links_plugin():
    """
    Test that the plugin only displays visible categories
    """
    category = get_default_category()
    context = get_jinja_context()
    plugin = CategoryLinksPlugin({"categories": [category.pk]})
    assert category not in plugin.get_context_data(context)["categories"]

    category.status = CategoryStatus.VISIBLE
    category.save()
    assert category in plugin.get_context_data(context)["categories"]


@pytest.mark.django_db
def test_category_links_plugin_show_all():
    """
    Test that show_all_categories forces plugin to return all visible categories
    """
    category = get_default_category()
    category.status = CategoryStatus.VISIBLE
    category.save()
    context = get_jinja_context()
    plugin = CategoryLinksPlugin({"show_all_categories": False})
    assert not plugin.get_context_data(context)["categories"]

    plugin = CategoryLinksPlugin({"show_all_categories": True})
    assert category in plugin.get_context_data(context)["categories"]
