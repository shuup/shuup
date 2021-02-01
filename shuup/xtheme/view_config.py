# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.utils.django_compat import force_text
from shuup.xtheme import XTHEME_GLOBAL_VIEW_NAME
from shuup.xtheme.layout import Layout
from shuup.xtheme.layout.utils import get_layout_data_key, get_provided_layouts
from shuup.xtheme.models import SavedViewConfig


class ViewConfig(object):
    """
    A view configuration.

    Contains layout and plugin configuration for all placeholders in a given view.

    This class does not directly correspond to a database model; it may act as a
    container for `SavedViewConfig` objects, and wraps the `SavedViewConfig` API.
    """

    def __init__(self, theme, shop, view_name, draft, global_type=False):
        """
        Initialize a view configuration.

        :param theme: Theme object (could be None to not touch the database).
        :type theme: shuup.xtheme.Theme|None
        :param shop: Shop object.
        :type shop: shuup.core.models.Shop
        :param view_name: View name (the class name of the view).
        :type view_name: str
        :param draft: Load in draft mode?
        :type draft: bool
        :param global_type: Boolean indicating whether this is a global config.
        :type global_type: bool|False
        """
        self.theme = theme
        self.shop = shop
        self.view_name = (XTHEME_GLOBAL_VIEW_NAME if global_type else force_text(view_name))
        self.draft = bool(draft)
        self._saved_view_config = None

    @property
    def saved_view_config(self):
        """
        Get a saved view config model depending on the current parameters.

        :return: A SavedViewConfig object for the current theme/view/draft mode, or None.
        :rtype: shuup.xtheme.models.SavedViewConfig|None
        """
        if not self.theme or not self.theme.identifier or not self.shop:
            return None

        if self._saved_view_config is None:
            self._saved_view_config = SavedViewConfig.objects.appropriate(
                theme=self.theme,
                shop=self.shop,
                view_name=self.view_name,
                draft=self.draft
            )
            self.draft = self._saved_view_config.draft
        return self._saved_view_config

    def get_placeholder_layouts(self, context, placeholder_name, default_layout={}):
        """
        Get a layout objects for the given placeholder and context.

        :param context: Rendering context.
        :type context: jinja2.runtime.Context
        :param placeholder_name: The name of the placeholder to load.
        :type placeholder_name: str
        :param default_layout: Default layout configuration (either a dict or an actual Layout).
        :type default_layout: dict|Layout
        :return: List of layouts available for current placeholder and context.
        :rtype: list
        """
        layouts = [
            self.get_placeholder_layout(
                Layout, placeholder_name, default_layout=default_layout, context=context)]

        for layout_cls in get_provided_layouts():
            layout = self.get_placeholder_layout(layout_cls, placeholder_name, context=context)
            if layout is not None:
                layouts.append(layout)

        return layouts

    def get_placeholder_layout(
            self, layout_cls, placeholder_name, default_layout={}, context=None, layout_data_key=None):
        """
        Get a layout object for the given placeholder.

        :param layout_cls:
        :type layout_cls:
        :param placeholder_name: The name of the placeholder to load.
        :type placeholder_name: str
        :param default_layout: Default layout configuration (either a dict or an actual Layout).
        :type default_layout: dict|Layout
        :param context: Rendering context.
        :type context: jinja2.runtime.Context
        :param layout_data_key: layout data key used for saving the layout data.
        :type layout_data_key: str
        :return: Layout.
        :rtype: Layout
        """
        svc = self.saved_view_config
        layout = layout_cls(self.theme, placeholder_name=placeholder_name)
        if not layout_data_key:
            if not layout.is_valid_context(context or {}):
                return
            layout_data_key = get_layout_data_key(placeholder_name, layout, context)

        if svc:
            placeholder_data = svc.get_layout_data(layout_data_key)
            if placeholder_data:
                return layout.unserialize(self.theme, placeholder_data, placeholder_name=placeholder_name)

        if default_layout:
            if isinstance(default_layout, Layout):
                return default_layout
            return layout.unserialize(self.theme, default_layout)

        return layout

    def save_default_placeholder_layout(self, placeholder_name, layout):
        """
        Save a default placeholder layout (only if no data for the PH already
        exists).

        :param placeholder_name: Placeholder name.
        :type placeholder_name: str
        :param layout: Layout or layout data.
        :type layout: Layout|dict
        :return: True if saved.
        :rtype: bool
        """
        if not self.draft:
            return False
        if self.saved_view_config and self.saved_view_config.get_layout_data(placeholder_name) is None:
            self.save_placeholder_layout(get_layout_data_key(placeholder_name, layout, {}), layout)
            return True
        return False

    def publish(self):
        """
        Publish this revision of the view configuration as the currently public one.

        :return: Success flag.
        :rtype: bool
        """
        svc = self.saved_view_config
        if not svc:
            raise ValueError("Error! Unable to publish view config. Is a theme set properly?")
        svc.publish()
        self.draft = svc.draft
        return True

    def revert(self):
        """
        Revert this revision of the view configuration, if it's a draft.

        :return: Success flag.
        :rtype: bool
        """
        svc = self.saved_view_config
        if not svc:
            raise ValueError("Error! Unable to revert view config. Is a theme set properly?")
        svc.revert()
        self.draft = True
        self._saved_view_config = None
        return True

    def save_placeholder_layout(self, layout_data_key, layout):
        """
        Save the given layout as the layout for the given placeholder.

        :param placeholder_name: The placeholder name.
        :type placeholder_name: str
        :param layout: Layout object (or dict).
        :type layout: Layout|dict
        """
        svc = self.saved_view_config
        if not svc:
            raise ValueError("Error! Unable to retrieve view config; unable to save data. Is a theme set properly?")
        svc.set_layout_data(layout_data_key, layout)
        svc.save()
