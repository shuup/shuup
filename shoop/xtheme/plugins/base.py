# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.template.loader import get_template
from django.utils.translation import ugettext_lazy as _

from shoop.apps.provides import get_identifier_to_object_map, get_provide_objects
from shoop.utils.text import space_case

SENTINEL = object()


class Plugin(object):
    """
    A plugin that can be instantiated within a `shoop.xtheme.layout.LayoutCell`.

    Other plugins should inherit from this class and register themselves in the
    `xtheme_plugin` provide category.
    """
    identifier = None
    fields = []
    required_context_variables = set()
    name = _("Plugin")  # User-visible name

    def __init__(self, config):
        """
        Instantiate a Plugin with the given `config` dictionary

        :param config: Dictionary of freeform configuration data
        :type config: dict
        """
        self.config = config

    def is_context_valid(self, context):
        """
        Check that the given rendering context is valid for rendering this plugin.

        By default, just checks `required_context_variables`.

        :param context: Rendering context
        :type context: jinja2.runtime.Context
        :return: True if we should bother trying to render this
        :rtype: bool
        """
        for key in self.required_context_variables:
            if context.get(key, SENTINEL) is SENTINEL:
                return False
        return True

    def render(self, context):
        """
        Return the HTML for a plugin in a given rendering context.

        :param context: Rendering context
        :type context: jinja2.runtime.Context
        :return: String of rendered content.
        :rtype: str
        """
        return ""  # pragma: no cover

    @classmethod
    def load(cls, identifier, default=None):
        return get_identifier_to_object_map("xtheme_plugin").get(identifier, default)

    @classmethod
    def get_plugin_choices(cls, empty_label=None):
        choices = []
        if empty_label:
            choices.append(("", empty_label))

        for plugin in get_provide_objects("xtheme_plugin"):
            if plugin.identifier:
                choices.append((
                    plugin.identifier,
                    getattr(plugin, "name", None) or plugin.identifier
                ))
        choices.sort()
        return choices


class TemplatedPlugin(Plugin):
    template_name = ""
    inherited_variables = set()
    config_copied_variables = set()
    engine = None  # template rendering engine

    def get_context_data(self, context):
        vars = {"request": context.get("request")}
        for key in self.required_context_variables:
            vars[key] = context.get(key)
        for key in self.inherited_variables:
            vars[key] = context.get(key)
        for key in self.config_copied_variables:
            vars[key] = self.config.get(key)
        return vars

    def render(self, context):
        vars = self.get_context_data(context)
        if self.engine:
            template = self.engine.get_template(self.template_name)
        else:
            template = get_template(self.template_name)
        return template.render(vars, request=context.get("request"))


def templated_plugin_factory(identifier, template_name, **kwargs):
    ns = {
        "identifier": identifier,
        "template_name": template_name,
    }
    ns.update(kwargs)
    ns.setdefault("name", space_case(identifier).title())
    return type(str("%sPlugin" % identifier), (TemplatedPlugin,), ns)
