# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from shoop.apps.provides import get_identifier_to_object_map


class Plugin(object):
    """
    A plugin that can be instantiated within a `shoop.xtheme.layout.LayoutCell`.

    Other plugins should inherit from this class and register themselves in the
    `xtheme_plugin` provide category.
    """
    identifier = None
    fields = []
    required_context_variables = set()

    def __init__(self, config):
        """
        Instantiate a Plugin with the given `config` dictionary
        :param config: Dictionary of freeform configuration data
        :type config: dict
        """
        self.config = config

    def render(self, context):
        """
        Return the HTML for a plugin in a given rendering context.

        :param context: Rendering context
        :type context: jinja2.runtime.Context
        :return: String of rendered content.
        :rtype: str
        """
        return ""

    @classmethod
    def load(cls, identifier, default=None):
        return get_identifier_to_object_map("xtheme_plugin").get(identifier, default)
