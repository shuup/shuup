# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import sys

import six
from django.conf import settings
from jinja2.environment import Environment, Template
from jinja2.utils import concat, internalcode

from shuup.apps.provides import get_provide_objects
from shuup.xtheme._theme import get_middleware_current_theme
from shuup.xtheme.editing import add_edit_resources
from shuup.xtheme.resources import (
    inject_resources, RESOURCE_CONTAINER_VAR_NAME, ResourceContainer
)


class XthemeTemplate(Template):
    """
    A subclass of Jinja templates with additional post-processing magic.
    """
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
            if ctx and ctx.name and ctx.name in settings.SHUUP_XTHEME_EXCLUDE_TEMPLATES_FROM_RESOUCE_INJECTION:
                return content

            return self._postprocess(ctx, content)
        except Exception:
            exc_info = sys.exc_info()
        return self.environment.handle_exception(exc_info, True)

    def _postprocess(self, context, content):
        # if the context contains the `allow_resource_injection` key and
        # it's value is False, we don't inject resources in the content
        if context and context.get("allow_resource_injection", True) is False:
            return content

        for inject_func in get_provide_objects("xtheme_resource_injection"):
            if callable(inject_func):
                inject_func(context, content)
        add_edit_resources(context)
        content = inject_resources(context, content)
        return content


class XthemeEnvironment(Environment):
    """
    Overrides the usual template class and allows dynamic switching of Xthemes.

    Enable by adding ``"environment": "shuup.xtheme.engine.XthemeEnvironment"``
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
        :rtype: shuup.xtheme.engine.XthemeTemplate
        """
        # Redirect to `get_or_select_template` to support live theme loading.
        return self.get_or_select_template(self._get_themed_template_names(name), parent=parent, globals=globals)

    @internalcode
    def get_or_select_template(self, template_name_or_list, parent=None, globals=None):
        """
        Does a typecheck and dispatches to :meth:`select_template` or :meth:`get_template`.

        :param template_name_or_list: Template name or list
        :type template_name_or_list: str|Iterable[str]
        :param parent: If the `parent` parameter is not `None`, :meth:`join_path` is called
                       to get the real template name before loading.
        :type parent: str|None
        :param globals: The `globals` parameter can be used to provide template wide globals.
                        These variables are available in the context at render time.
        :return: Template object
        :rtype: shuup.xtheme.engine.XthemeTemplate
        """
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
        `shuup/front/bar.jinja`, we'll look at `mystery/shuup/front/bar.jinja`, finally at `shuup/front/bar.jinja`.

        Mystery theme also can define default template dir let's say `pony`. In this scenario we're looking up
        `shuup/front/bar.jinja` from `mystery/shuup/front/bar.jinja` then at `pony/shuup/front/bar.jinja` and
        finally at the default `shuup/front/bar.jinja`.

        :param name: Template name
        :type name: str
        :return: A template name or a list thereof
        :rtype: str|list[str]
        """
        if name.startswith("shuup/admin"):  # Ignore the admin.
            return name

        # we strongly depend on the XthemMiddleware as it should set the current theme
        # for this thread based on the request it processes
        theme = get_middleware_current_theme()
        if not theme:
            return name
        theme_template = "%s/%s" % ((theme.template_dir or theme.identifier), name)
        default_template = (("%s/%s" % (theme.default_template_dir, name)) if theme.default_template_dir else None)
        return [theme_template, default_template, name] if default_template else [theme_template, name]
