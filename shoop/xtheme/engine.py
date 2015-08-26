# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals
import sys

import six
from jinja2.environment import Environment, Template
from jinja2.utils import concat, internalcode

from shoop.xtheme.resources import RESOURCE_CONTAINER_VAR_NAME, ResourceContainer, inject_resources
from shoop.xtheme.theme import get_current_theme


class XthemeTemplate(Template):
    def render(self, *args, **kwargs):
        """
        Render the template and postprocess it.

        :return: Rendered markup
        :rtype: str
        """
        vars = dict(*args, **kwargs)
        vars[RESOURCE_CONTAINER_VAR_NAME] = ResourceContainer()
        ctx = self.new_context(vars)
        try:
            content = concat(self.root_render_func(ctx))
            return self._postprocess(ctx, content)
        except Exception:
            exc_info = sys.exc_info()
        return self.environment.handle_exception(exc_info, True)

    def _postprocess(self, context, content):
        # TODO: Add a hook here for addons to inject resources without plugins
        content = inject_resources(context, content)
        return content


class XthemeEnvironment(Environment):
    """
    Overrides the usual template class and allows dynamic switching of Xthemes.

    Enable by adding ``"environment": "shoop.xtheme.engine.XthemeEnvironment"``
    in your ``TEMPLATES`` settings.
    """

    # The Jinja2 source says:
    # > hook in default template class.  if anyone reads this comment: ignore that
    # > it's possible to use custom templates ;-)
    # Well, I ain't ignoring that.

    template_class = XthemeTemplate

    def get_template(self, name, parent=None, globals=None):
        """
        Load a template from the loader.  If a loader is configured this
        method asks the loader for the template and returns a :class:`Template`.

        :param name: Template name.
        :type name: str
        :param parent: If the `parent` parameter is not `None`, :meth:`join_path` is called
                       to get the real template name before loading.
        :type parent: str|None
        :param globals: The `globals` parameter can be used to provide template wide globals.
                        These variables are available in the context at render time.
        :type globals: dict|None
        :return: Template object
        :rtype: shoop.xtheme.engine.XthemeTemplate
        """
        # Redirect to `get_or_select_template` to support live theme loading.
        return self.get_or_select_template(self._get_themed_template_names(name), parent=parent, globals=globals)

    @internalcode
    def get_or_select_template(self, template_name_or_list, parent=None, globals=None):
        # Overridden to redirect calls to super.
        if isinstance(template_name_or_list, six.string_types):
            return super(XthemeEnvironment, self).get_template(template_name_or_list, parent, globals)
        elif isinstance(template_name_or_list, Template):
            return template_name_or_list
        return super(XthemeEnvironment, self).select_template(template_name_or_list, parent, globals)

    def _get_themed_template_names(self, name):
        """
        Get theme-prefixed paths for the given template name.

        For instance, if the template_dir or identifier of the current theme is `mystery` and we're looking up
        `shoop/front/bar.jinja`, we'll look at `mystery/shoop/front/bar.jinja`, then at `shoop/front/bar.jinja`.

        :param name: Template name
        :type name: str
        :return: A template name or a list thereof
        :rtype: str|list[str]
        """
        if name.startswith("shoop/admin"):  # Ignore the admin.
            return name
        theme = get_current_theme()
        return [
            "%s/%s" % ((theme.template_dir or theme.identifier), name),
            name
        ]
