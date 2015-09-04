# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from jinja2.utils import contextfunction

from shoop.xtheme.editing import is_edit_mode
from shoop.xtheme.rendering import get_view_config
from shoop.xtheme.theme import get_current_theme


class XthemeNamespace(object):
    @contextfunction
    def get_view_name(self, context):
        return get_view_config(context).view_name

    @contextfunction
    def is_edit_mode(self, context):
        return is_edit_mode(context["request"])

    @contextfunction
    def get(self, context, name, default=None):
        """
        Get a theme setting value.

        :param context: Implicit Jinja2 context
        :type context: jinja2.runtime.Context
        :param name: Setting name
        :type name: str
        :param default: Default value if setting is not found
        :type default: object
        :return: Value
        :rtype: object
        """
        request = context["request"]
        theme = get_current_theme(request)
        if theme:
            return theme.get_setting(name, default=default)
        return default
