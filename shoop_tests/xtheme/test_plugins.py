# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.xtheme import resources
from shoop.xtheme.plugins.snippets import SnippetsPlugin


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
