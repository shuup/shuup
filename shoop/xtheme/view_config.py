# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.encoding import force_text

from shoop.xtheme.layout import Layout


class ViewConfig(object):
    """
    A view configuration.

    Contains layout and plugin configuration for all placeholders in a given view.
    """

    def __init__(self, view_name):
        """
        Initialize a view configuration.

        :param view_name: View name (the class name of the view)
        :type view_name: str
        """
        self.view_name = force_text(view_name)

    def get_placeholder_layout(self, placeholder_name, default_layout=None):
        """
        Get a Layout object for the given placeholder.

        :param placeholder_name: The name of the placeholder to load.
        :type placeholder_name: str
        :param default_layout: Default layout configuration (either a dict or an actual Layout)
        :type default_layout: dict|Layout
        :return: Layout
        :rtype: Layout
        """
        # TODO: Add actual loading
        if default_layout:
            if isinstance(default_layout, Layout):
                return default_layout
            return Layout.unserialize(default_layout)
        return Layout(placeholder_name=placeholder_name)
