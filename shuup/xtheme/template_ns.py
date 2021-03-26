# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from jinja2.utils import contextfunction

from shuup.xtheme._theme import get_current_theme, get_middleware_current_theme
from shuup.xtheme.editing import is_edit_mode
from shuup.xtheme.rendering import get_view_config


class XthemeNamespace(object):
    """
    A template helper namespace for Xtheme-related functionality.
    """

    @contextfunction
    def get_view_name(self, context):
        """
        Get the current view's view name (used for identifying view configurations).

        :param context: Implicit Jinja2 context
        :type context: jinja2.runtime.Context
        :return: View name string
        :rtype: str
        """
        return get_view_config(context).view_name

    @contextfunction
    def is_edit_mode(self, context):
        """
        Get the current edit mode status.

        :param context: Implicit Jinja2 context
        :type context: jinja2.runtime.Context
        :return: Edit mode enable flag
        :rtype: bool
        """

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
        theme = getattr(request, "theme", None) or get_current_theme(request.shop)
        if theme:
            return theme.get_setting(name, default=default)
        return default

    def __getitem__(self, item):
        """
        Look for additional helper callables in the active theme.

        Callables marked with the Django standard `alters_data` attribute will not be honored.

        :param item: Template helper name
        :type item: str
        :return: Template helper, maybe
        :rtype: object|None
        """
        theme = get_middleware_current_theme()
        if theme:
            helper = getattr(theme, item, None)
            if helper and callable(helper) and not getattr(helper, "alters_data", False):
                return helper
        raise KeyError("No such template helper: %s" % item)
